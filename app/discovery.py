"""
Network Topology Discovery Engine
Recursively discovers network topology using CDP/LLDP
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

from device_detector import DeviceTypeDetector
from parsers import parse_cdp_neighbors_detail, parse_lldp_neighbors_detail, merge_neighbor_info
from mock_devices import is_mock_mode, get_mock_connection

logger = logging.getLogger(__name__)


@dataclass
class Device:
    """Represents a discovered network device"""
    hostname: str
    mgmt_ip: Optional[str] = None
    device_type: Optional[str] = None
    platform: Optional[str] = None
    links: List['Link'] = field(default_factory=list)


@dataclass
class Link:
    """Represents a connection between two devices"""
    local_device: str
    local_intf: str
    remote_device: str
    remote_intf: str
    remote_ip: Optional[str] = None
    protocols: List[str] = field(default_factory=list)


@dataclass
class Topology:
    """Network topology graph"""
    devices: Dict[str, Device] = field(default_factory=dict)
    
    def add_device(self, hostname: str, mgmt_ip: str = None, device_type: str = None, platform: str = None):
        """Add a device to the topology"""
        if hostname not in self.devices:
            self.devices[hostname] = Device(
                hostname=hostname,
                mgmt_ip=mgmt_ip,
                device_type=device_type,
                platform=platform
            )
    
    def add_link(self, link: Link):
        """Add a link and ensure both devices exist"""
        # Ensure devices exist
        if link.local_device not in self.devices:
            self.devices[link.local_device] = Device(hostname=link.local_device)
        if link.remote_device not in self.devices:
            self.devices[link.remote_device] = Device(hostname=link.remote_device, mgmt_ip=link.remote_ip)
        
        # Add link to local device
        self.devices[link.local_device].links.append(link)


class DiscoveryError(Exception):
    """Exception raised during discovery"""
    def __init__(self, message: str, error_type: str = "generic"):
        super().__init__(message)
        self.message = message
        self.error_type = error_type


class TopologyDiscoverer:
    """Discovers network topology recursively"""
    
    def __init__(self, device_detector: DeviceTypeDetector, max_depth: int = 3):
        self.detector = device_detector
        self.max_depth = max_depth
        self.topology = Topology()
        self.visited: Set[str] = set()
        self.credentials = {}
    
    def discover(self, seed_ip: str, seed_device_type: str, username: str, password: str) -> Topology:
        """
        Start topology discovery from a seed device
        
        Args:
            seed_ip: IP address of seed device
            seed_device_type: Netmiko device type for seed
            username: SSH username
            password: SSH password
            
        Returns:
            Discovered Topology object
        """
        self.credentials = {'username': username, 'password': password}
        self.topology = Topology()
        self.visited = set()
        
        # Queue: (ip, device_type, depth)
        queue = deque([(seed_ip, seed_device_type, 0)])
        
        logger.info(f"Starting discovery from {seed_ip} (type: {seed_device_type})")
        
        while queue:
            ip, device_type, depth = queue.popleft()
            
            # Skip if already visited or too deep
            if ip in self.visited or depth > self.max_depth:
                continue
            
            self.visited.add(ip)
            logger.info(f"Discovering {ip} at depth {depth}")
            
            try:
                # Connect to device
                conn = self._connect(ip, device_type)
                
                # Get hostname
                hostname = self._get_hostname(conn)
                logger.info(f"Connected to {hostname} ({ip})")
                
                # Add device to topology
                self.topology.add_device(hostname, ip, device_type)
                
                # Discover neighbors
                neighbors = self._discover_neighbors(conn, hostname)
                
                # Process each neighbor
                for neighbor in neighbors:
                    # Create link
                    link = Link(
                        local_device=hostname,
                        local_intf=neighbor.get('local_intf', '?'),
                        remote_device=neighbor.get('remote_device', 'Unknown'),
                        remote_intf=neighbor.get('remote_intf', '?'),
                        remote_ip=neighbor.get('remote_ip'),
                        protocols=neighbor.get('protocols', [])
                    )
                    self.topology.add_link(link)
                    
                    # Determine device type for neighbor
                    neighbor_device_type = self._detect_neighbor_type(neighbor)
                    
                    # Queue for discovery if we detected a type and have an IP
                    if neighbor_device_type and neighbor.get('remote_ip'):
                        if neighbor['remote_ip'] not in self.visited:
                            queue.append((neighbor['remote_ip'], neighbor_device_type, depth + 1))
                            logger.info(f"Queued {neighbor['remote_device']} ({neighbor['remote_ip']}) as {neighbor_device_type}")
                    else:
                        logger.debug(f"Skipping {neighbor.get('remote_device', 'Unknown')}: type={neighbor_device_type}, ip={neighbor.get('remote_ip')}")
                
                conn.disconnect()
                
            except DiscoveryError as e:
                logger.error(f"Discovery error for {ip}: {e.message}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error discovering {ip}: {e}")
                continue
        
        logger.info(f"Discovery complete. Found {len(self.topology.devices)} devices")
        return self.topology
    
    def _connect(self, ip: str, device_type: str) -> ConnectHandler:
        """Connect to a device via SSH (or mock for testing)"""
        # Check if this is a mock device
        if is_mock_mode(ip):
            logger.info(f"Using MOCK mode for {ip}")
            return get_mock_connection(ip, device_type, 
                                      self.credentials['username'],
                                      self.credentials['password'])
        
        # Real SSH connection
        try:
            conn = ConnectHandler(
                device_type=device_type,
                host=ip,
                username=self.credentials['username'],
                password=self.credentials['password'],
                timeout=15,
                fast_cli=True,
            )
            return conn
        except NetmikoTimeoutException:
            raise DiscoveryError(f"Connection timeout to {ip}", "timeout")
        except NetmikoAuthenticationException:
            raise DiscoveryError(f"Authentication failed to {ip}", "auth")
        except Exception as e:
            raise DiscoveryError(f"Connection error to {ip}: {e}", "connection")
    
    def _get_hostname(self, conn: ConnectHandler) -> str:
        """Extract hostname from device prompt"""
        prompt = conn.find_prompt()
        # Remove trailing # or >
        hostname = prompt.rstrip('#>').strip()
        return hostname
    
    def _discover_neighbors(self, conn: ConnectHandler, hostname: str) -> List[Dict]:
        """Discover neighbors using CDP and LLDP"""
        cdp_neighbors = []
        lldp_neighbors = []
        
        # Try CDP
        try:
            cdp_output = conn.send_command("show cdp neighbors detail", read_timeout=30)
            cdp_neighbors = parse_cdp_neighbors_detail(cdp_output)
            logger.info(f"Found {len(cdp_neighbors)} CDP neighbors on {hostname}")
        except Exception as e:
            logger.warning(f"CDP discovery failed on {hostname}: {e}")
        
        # Try LLDP
        try:
            lldp_output = conn.send_command("show lldp neighbors detail", read_timeout=30)
            lldp_neighbors = parse_lldp_neighbors_detail(lldp_output)
            logger.info(f"Found {len(lldp_neighbors)} LLDP neighbors on {hostname}")
        except Exception as e:
            logger.warning(f"LLDP discovery failed on {hostname}: {e}")
        
        # Merge CDP and LLDP information
        merged = merge_neighbor_info(cdp_neighbors, lldp_neighbors)
        return merged
    
    def _detect_neighbor_type(self, neighbor: Dict) -> Optional[str]:
        """Detect Netmiko device type for a neighbor"""
        platform = neighbor.get('remote_platform', '')
        capabilities = neighbor.get('remote_capabilities', '')
        system_desc = neighbor.get('system_description', '')
        
        # Try CDP-based detection first (has better platform info)
        if platform:
            device_type = self.detector.detect_from_cdp(platform, capabilities)
            if device_type:
                return device_type
        
        # Fall back to LLDP system description
        if system_desc:
            device_type = self.detector.detect_from_lldp(system_desc, capabilities)
            if device_type:
                return device_type
        
        return None


def render_topology_tree(topology: Topology, root: str = None) -> str:
    """
    Render topology as a text tree with interface and IP labels
    
    Args:
        topology: Topology object
        root: Root device hostname (if None, picks first device)
        
    Returns:
        Multi-line string representation
    """
    if not topology.devices:
        return "No devices discovered"
    
    # Build adjacency graph
    adjacency = {}
    link_details = {}  # Store link info for display
    
    for device in topology.devices.values():
        adjacency.setdefault(device.hostname, set())
        for link in device.links:
            adjacency[link.local_device].add(link.remote_device)
            adjacency.setdefault(link.remote_device, set()).add(link.local_device)
            
            # Store link details for both directions
            key = (link.local_device, link.remote_device)
            link_details[key] = {
                'local_intf': link.local_intf,
                'remote_intf': link.remote_intf,
                'remote_ip': link.remote_ip,
                'protocols': link.protocols
            }
    
    # Choose root
    if root is None:
        root = next(iter(adjacency))
    
    # Build tree representation
    lines = []
    visited = set()
    
    def build_tree(node: str, prefix: str = "", is_last: bool = True):
        """Recursively build tree structure"""
        visited.add(node)
        
        # Add device with IP
        device = topology.devices.get(node)
        device_label = node
        if device and device.mgmt_ip:
            device_label = f"{node} ({device.mgmt_ip})"
        
        lines.append(f"{prefix}{device_label}")
        
        # Get unvisited neighbors
        neighbors = sorted(adjacency.get(node, set()) - visited)
        
        for i, neighbor in enumerate(neighbors):
            is_last_neighbor = (i == len(neighbors) - 1)
            
            # Get link details
            link_info = link_details.get((node, neighbor), {})
            local_intf = link_info.get('local_intf', '?')
            remote_intf = link_info.get('remote_intf', '?')
            remote_ip = link_info.get('remote_ip', '')
            protocols = '+'.join(link_info.get('protocols', []))
            
            # Build connection line
            connector = "└─" if is_last_neighbor else "├─"
            protocol_label = f"[{protocols}]" if protocols else ""
            
            # Show interface mapping
            connection_line = f"{prefix}{'   ' if is_last else '│  '}{connector}{protocol_label} {local_intf} ↔ {remote_intf}"
            if remote_ip:
                connection_line += f" ({remote_ip})"
            
            lines.append(connection_line)
            
            # Recurse
            new_prefix = prefix + ("   " if is_last else "│  ") + ("   " if is_last_neighbor else "│  ")
            build_tree(neighbor, new_prefix, is_last_neighbor)
    
    build_tree(root)
    return "\n".join(lines)
