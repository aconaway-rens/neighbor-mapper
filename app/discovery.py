"""
Network Topology Discovery Engine
Recursively discovers network topology using CDP/LLDP and L3 routing protocols
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

from device_detector import DeviceTypeDetector
from parsers import (parse_cdp_neighbors_detail, parse_lldp_neighbors_detail,
                     merge_neighbor_info, parse_l3_neighbors)
from mock_devices import is_mock_mode, get_mock_connection

logger = logging.getLogger(__name__)

# L3 routing protocol commands per device type.
# Each protocol key maps to the command that lists established neighbors.
L3_COMMANDS = {
    'cisco_ios': {
        'ospf':  'show ip ospf neighbor',
        'eigrp': 'show ip eigrp neighbors',
        'bgp':   'show ip bgp neighbors',
        'isis':  'show isis neighbors',
    },
    'cisco_xe': {
        'ospf':  'show ip ospf neighbor',
        'eigrp': 'show ip eigrp neighbors',
        'bgp':   'show ip bgp neighbors',
        'isis':  'show isis neighbors',
    },
    'cisco_nxos': {
        'ospf':  'show ip ospf neighbors',
        'eigrp': 'show ip eigrp neighbors',
        'bgp':   'show bgp ipv4 unicast neighbors',
        'isis':  'show isis adjacency',
    },
    'arista_eos': {
        'ospf':  'show ip ospf neighbor',
        'bgp':   'show ip bgp neighbors',
        'isis':  'show isis neighbors',
    },
    'juniper_junos': {
        'ospf':  'show ospf neighbor',
        'bgp':   'show bgp neighbor',
        'isis':  'show isis adjacency',
    },
    'extreme': {
        'ospf':  'show ospf neighbor',
        'bgp':   'show bgp neighbor',
    },
    'default': {
        'ospf':  'show ip ospf neighbor',
        'eigrp': 'show ip eigrp neighbors',
        'bgp':   'show ip bgp neighbors',
        'isis':  'show isis neighbors',
    },
}


@dataclass
class Device:
    """Represents a discovered network device"""
    hostname: str
    mgmt_ip: Optional[str] = None
    device_type: Optional[str] = None  # Netmiko device type (e.g., "cisco_ios")
    device_category: Optional[str] = None  # Category (e.g., "router", "switch", "firewall")
    has_routing: bool = False  # Whether device has routing capabilities (for L3 switches)
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
    remote_device_category: Optional[str] = None  # Category of remote device
    remote_has_routing: bool = False  # Whether remote device has routing capabilities
    protocols: List[str] = field(default_factory=list)


@dataclass
class Topology:
    """Network topology graph"""
    devices: Dict[str, Device] = field(default_factory=dict)
    
    def add_device(self, hostname: str, mgmt_ip: str = None, device_type: str = None, device_category: str = None, platform: str = None):
        """Add a device to the topology"""
        if hostname not in self.devices:
            self.devices[hostname] = Device(
                hostname=hostname,
                mgmt_ip=mgmt_ip,
                device_type=device_type,
                device_category=device_category,
                platform=platform
            )
    
    def add_link(self, link: Link):
        """Add a link and ensure both devices exist"""
        # Ensure devices exist
        if link.local_device not in self.devices:
            self.devices[link.local_device] = Device(hostname=link.local_device)
        if link.remote_device not in self.devices:
            self.devices[link.remote_device] = Device(
                hostname=link.remote_device, 
                mgmt_ip=link.remote_ip,
                device_category=link.remote_device_category,
                has_routing=link.remote_has_routing
            )
        # If device exists but doesn't have category/routing, update it
        elif link.remote_device_category and not self.devices[link.remote_device].device_category:
            self.devices[link.remote_device].device_category = link.remote_device_category
            self.devices[link.remote_device].has_routing = link.remote_has_routing
        
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
    
    def __init__(self, device_detector: DeviceTypeDetector, max_depth: int = 3, filters: dict = None):
        self.detector = device_detector
        self.max_depth = max_depth
        self.filters = filters or {
            'include_routers': True,
            'include_switches': True,
            'include_phones': False,
            'include_servers': False,
            'include_aps': False,
            'include_other': False,
            'include_l3': False,
        }
        self.topology = Topology()
        self.visited: Set[str] = set()
        self.failed: Dict[str, str] = {}  # Track failed devices {ip: reason}
        self.credentials = {}
        logger.info(f"TopologyDiscoverer initialized with filters: {self.filters}")
    
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
            
            logger.info(f"Queue size: {len(queue)} | Processing: {ip} at depth {depth}")
            
            # Skip if already visited or too deep
            if ip in self.visited or depth > self.max_depth:
                if ip in self.visited:
                    logger.info(f"Already visited {ip}, skipping")
                if depth > self.max_depth:
                    logger.info(f"Depth {depth} exceeds max_depth {self.max_depth}, skipping")
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
                neighbors = self._discover_neighbors(conn, hostname, device_type)
                
                # Process each neighbor
                for neighbor in neighbors:
                    # Determine device type and category for neighbor
                    neighbor_info = self._detect_neighbor_type(neighbor)
                    
                    # Skip if no device type could be detected
                    if not neighbor_info:
                        logger.info(f"⊗ Skipping {neighbor.get('remote_device', 'Unknown')}: no device type detected")
                        continue
                    
                    neighbor_device_type, neighbor_device_category, neighbor_has_routing = neighbor_info
                    
                    # Check if this device type should be included based on filters
                    should_include = False
                    if neighbor_device_category == 'router':
                        should_include = self.filters.get('include_routers', False)
                    elif neighbor_device_category == 'firewall':
                        should_include = self.filters.get('include_routers', False)
                    elif neighbor_device_category == 'switch':
                        should_include = self.filters.get('include_switches', False)
                    elif neighbor_device_category == 'phone':
                        should_include = self.filters.get('include_phones', False)
                    elif neighbor_device_category == 'server':
                        should_include = self.filters.get('include_servers', False)
                    elif neighbor_device_category == 'access_point':
                        should_include = self.filters.get('include_aps', False)
                    else:
                        should_include = self.filters.get('include_other', False)
                    
                    if not should_include:
                        logger.info(f"⊗ Skipping {neighbor.get('remote_device', 'Unknown')}: {neighbor_device_category} filtered out by user settings")
                        continue
                    
                    # Log what we found
                    logger.info(f"Neighbor: {neighbor.get('remote_device', 'Unknown')} - Type: {neighbor_device_type} - Category: {neighbor_device_category} - L3: {neighbor_has_routing} - Caps: {neighbor.get('remote_capabilities', 'None')}")
                    
                    # Create link and add to topology
                    # Use IP as device name for L3-only neighbors that have no hostname yet
                    remote_name = (neighbor.get('remote_device')
                                   or neighbor.get('remote_ip')
                                   or 'Unknown')
                    link = Link(
                        local_device=hostname,
                        local_intf=neighbor.get('local_intf') or '?',
                        remote_device=remote_name,
                        remote_intf=neighbor.get('remote_intf') or '?',
                        remote_ip=neighbor.get('remote_ip'),
                        remote_device_category=neighbor_device_category,
                        remote_has_routing=neighbor_has_routing,
                        protocols=neighbor.get('protocols', [])
                    )
                    self.topology.add_link(link)
                    logger.info(f"✓ Added link: {hostname} ↔ {neighbor.get('remote_device', 'Unknown')}")
                    
                    # Queue for discovery if we have an IP AND device should be crawled
                    if neighbor.get('remote_ip'):
                        capabilities = neighbor.get('remote_capabilities', '')
                        should_crawl = self.detector._should_crawl(capabilities, self.filters)
                        
                        if should_crawl:
                            if neighbor['remote_ip'] not in self.visited:
                                queue.append((neighbor['remote_ip'], neighbor_device_type, depth + 1))
                                logger.info(f"→ Queued {neighbor['remote_device']} ({neighbor['remote_ip']}) as {neighbor_device_type} for depth {depth + 1}")
                            else:
                                logger.info(f"⊗ Already visited {neighbor['remote_ip']}")
                        else:
                            logger.info(f"⊗ Not queuing {neighbor.get('remote_device', 'Unknown')}: non-crawlable device type ({neighbor_device_category})")
                    else:
                        logger.info(f"⊗ Not queuing {neighbor.get('remote_device', 'Unknown')}: no IP address")
                
                conn.disconnect()
                
            except DiscoveryError as e:
                logger.error(f"Discovery error for {ip}: {e.message}")
                self.failed[ip] = e.message
                continue
            except Exception as e:
                logger.error(f"Unexpected error discovering {ip}: {e}")
                self.failed[ip] = str(e)
                continue
        
        logger.info(f"Discovery complete. Found {len(self.topology.devices)} devices, {len(self.failed)} failed")
        if self.failed:
            logger.warning(f"Failed devices: {self.failed}")
        return self.topology
    
    def _connect(self, ip: str, device_type: str) -> ConnectHandler:
        """Connect to a device via SSH (or mock for testing)"""
        # Check if this is a mock device
        if is_mock_mode(ip):
            logger.info(f"Using MOCK mode for {ip}")
            return get_mock_connection(ip, device_type, 
                                      self.credentials['username'],
                                      self.credentials['password'])
        
        # Real SSH connection with device type fallback
        logger.info(f"Connecting to {ip} with device_type={device_type}, username={self.credentials['username']}")
        
        # Try primary device type first
        device_types_to_try = [device_type]
        
        # Add fallbacks for common device types
        if device_type == 'cisco_ios':
            device_types_to_try.extend(['cisco_xe', 'cisco_nxos'])
        elif device_type == 'cisco_xe':
            device_types_to_try.extend(['cisco_ios'])
        elif device_type == 'cisco_nxos':
            device_types_to_try.extend(['cisco_ios'])
        elif device_type == 'hp_procurve':
            device_types_to_try.extend(['hp_comware', 'aruba_os'])
        elif device_type == 'hp_comware':
            device_types_to_try.extend(['hp_procurve', 'aruba_os'])
        elif device_type == 'aruba_os':
            device_types_to_try.extend(['hp_procurve'])
        elif device_type == 'dell_os10':
            device_types_to_try.extend(['dell_force10'])
        elif device_type == 'dell_force10':
            device_types_to_try.extend(['dell_os10'])
        elif device_type == 'extreme':
            device_types_to_try.extend(['extreme_vsp'])
        elif device_type == 'extreme_vsp':
            device_types_to_try.extend(['extreme'])
        elif device_type == 'ubiquiti_edge':
            device_types_to_try.extend(['ubiquiti_unifi'])
        
        last_error = None
        
        for dt in device_types_to_try:
            try:
                if dt != device_type:
                    logger.info(f"  Trying fallback device_type={dt}")
                
                conn = ConnectHandler(
                    device_type=dt,
                    host=ip,
                    username=self.credentials['username'],
                    password=self.credentials['password'],
                    timeout=10,           # Reduced from 30
                    session_timeout=20,   # Reduced from 60
                    auth_timeout=10,      # Reduced from 30
                    banner_timeout=10,    # Reduced from 20
                    fast_cli=True,        # Changed from False - speeds up commands
                    global_delay_factor=1, # Reduced from 2
                )
                logger.info(f"✓ Successfully connected to {ip} using device_type={dt}")
                return conn
            except NetmikoTimeoutException as e:
                # Don't try other device types for timeout - the device isn't reachable
                logger.error(f"✗ Connection timeout to {ip}")
                raise DiscoveryError(f"Connection timeout to {ip}", "timeout")
            except NetmikoAuthenticationException as e:
                # Don't try other device types for auth failures
                logger.error(f"✗ Authentication failed to {ip}")
                raise DiscoveryError(f"Authentication failed to {ip}", "auth")
            except Exception as e:
                last_error = f"{type(e).__name__}: {str(e)}"
                logger.warning(f"  Failed with device_type={dt}: {type(e).__name__}")
                continue
        
        # All device types failed
        logger.error(f"✗ Failed to connect to {ip} with all device types. Last error: {last_error}")
        raise DiscoveryError(f"Connection failed to {ip} (tried {device_types_to_try}): {last_error}", "connection")
    
    def _get_hostname(self, conn: ConnectHandler) -> str:
        """Extract hostname from device prompt"""
        prompt = conn.find_prompt()
        # Remove trailing # or >
        hostname = prompt.rstrip('#>').strip()
        return hostname
    
    def _discover_neighbors(self, conn: ConnectHandler, hostname: str,
                            device_type: str = None) -> List[Dict]:
        """Discover neighbors using CDP, LLDP, and optionally L3 routing protocols"""
        cdp_neighbors = []
        lldp_neighbors = []

        # Try CDP
        try:
            cdp_output = conn.send_command("show cdp neighbors detail", read_timeout=15)
            cdp_neighbors = parse_cdp_neighbors_detail(cdp_output)
            logger.info(f"Found {len(cdp_neighbors)} CDP neighbors on {hostname}")
        except Exception as e:
            logger.warning(f"CDP discovery failed on {hostname}: {e}")

        # Try LLDP
        try:
            lldp_output = conn.send_command("show lldp neighbors detail", read_timeout=15)
            lldp_neighbors = parse_lldp_neighbors_detail(lldp_output)
            logger.info(f"Found {len(lldp_neighbors)} LLDP neighbors on {hostname}")
        except Exception as e:
            logger.warning(f"LLDP discovery failed on {hostname}: {e}")

        # Try L3 routing protocols (optional, controlled by filter)
        l3_neighbors = []
        if self.filters.get('include_l3', False):
            commands = L3_COMMANDS.get(device_type, L3_COMMANDS['default'])
            for protocol, command in commands.items():
                try:
                    output = conn.send_command(command, read_timeout=15)
                    parsed = parse_l3_neighbors(output, protocol)
                    if parsed:
                        logger.info(f"Found {len(parsed)} {protocol.upper()} neighbors on {hostname}")
                    l3_neighbors.extend(parsed)
                except Exception as e:
                    logger.debug(f"L3 {protocol.upper()} discovery failed on {hostname}: {e}")

        # Merge all neighbor sources
        merged = merge_neighbor_info(cdp_neighbors, lldp_neighbors, l3_neighbors)
        return merged
    
    def _detect_neighbor_type(self, neighbor: Dict) -> Optional[tuple]:
        """
        Detect Netmiko device type and category for a neighbor
        
        Returns:
            Tuple of (device_type, device_category, has_routing) or None if filtered
        """
        platform = neighbor.get('remote_platform') or ''
        capabilities = neighbor.get('remote_capabilities') or ''
        system_desc = neighbor.get('system_description') or ''
        
        # Parse capabilities into a set
        caps = set()
        if capabilities:
            # Handle both "Router Switch" and "R,S" formats
            cap_str = capabilities.replace(',', ' ').upper()
            caps = set(cap_str.split())
        
        # Get device category and routing capability (pass platform and system_desc for firewall detection)
        device_category, has_routing = self.detector._categorize_device(caps, platform, system_desc) if (caps or platform or system_desc) else ('unknown', False)
        
        # Try CDP-based detection first (has better platform info)
        if platform:
            device_type = self.detector.detect_from_cdp(platform, capabilities, self.filters)
            if device_type:
                return (device_type, device_category, has_routing)
        
        # Fall back to LLDP system description
        if system_desc:
            device_type = self.detector.detect_from_lldp(system_desc, capabilities, self.filters)
            if device_type:
                return (device_type, device_category, has_routing)

        # Fallback for L3-only neighbors: no platform or system_desc, but we know the category
        # from capabilities (e.g. remote_capabilities='Router' set by L3 parsers).
        # Use detector default type so the device can be queued for SSH discovery.
        if device_category and device_category != 'unknown':
            return (self.detector.default_type, device_category, has_routing)

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
