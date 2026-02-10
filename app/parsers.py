"""
CDP and LLDP Neighbor Parsers
Extract neighbor information from show command output
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


def parse_cdp_neighbors_detail(output: str) -> List[Dict[str, str]]:
    """
    Parse 'show cdp neighbors detail' output
    
    Returns list of neighbor dicts with keys:
    - remote_device: Neighbor hostname
    - remote_ip: Management IP address
    - remote_platform: Platform string
    - remote_capabilities: Device capabilities
    - local_intf: Local interface
    - remote_intf: Remote interface
    """
    neighbors = []
    current = {}
    
    for line in output.splitlines():
        line_stripped = line.strip()
        
        # New neighbor entry
        if line_stripped.startswith("Device ID:"):
            if current:
                neighbors.append(current)
                current = {}
            device_id = line_stripped.split("Device ID:")[1].strip()
            # Sometimes includes domain, strip it
            current["remote_device"] = device_id.split('.')[0]
        
        # IP address (multiple formats: "IP address:", "IPv4 Address:", etc.)
        elif "IP address:" in line_stripped or "IPv4 Address:" in line_stripped:
            # Handle both "IP address: X.X.X.X" and "IPv4 Address: X.X.X.X"
            if "IPv4 Address:" in line_stripped:
                ip = line_stripped.split("IPv4 Address:")[1].strip()
            else:
                ip = line_stripped.split("IP address:")[1].strip()
            
            if ip and not ip.startswith("("):  # Skip "(not available)" or similar
                current["remote_ip"] = ip
        
        # Platform and capabilities
        elif line_stripped.startswith("Platform:"):
            parts = line_stripped.split(",")
            platform = parts[0].split("Platform:")[1].strip()
            current["remote_platform"] = platform
            
            # Capabilities might be on same line
            for part in parts:
                if "Capabilities:" in part:
                    caps = part.split("Capabilities:")[1].strip()
                    current["remote_capabilities"] = caps
        
        # Interface mapping
        elif line_stripped.startswith("Interface:"):
            # Format: "Interface: GigabitEthernet1/0/1,  Port ID (outgoing port): GigabitEthernet0/1"
            parts = line_stripped.split(",")
            local_intf = parts[0].split("Interface:")[1].strip()
            current["local_intf"] = local_intf
            
            if len(parts) > 1 and "Port ID" in parts[1]:
                remote_intf = parts[1].split(":")[-1].strip()
                current["remote_intf"] = remote_intf
    
    # Don't forget the last neighbor
    if current:
        neighbors.append(current)
    
    # Log what we extracted
    logger.info(f"Parsed {len(neighbors)} CDP neighbors")
    for i, n in enumerate(neighbors):
        logger.debug(f"  CDP Neighbor {i+1}: {n.get('remote_device', '?')} - IP: {n.get('remote_ip', 'MISSING')} - Platform: {n.get('remote_platform', '?')}")
    
    return neighbors


def parse_lldp_neighbors_detail(output: str) -> List[Dict[str, str]]:
    """
    Parse 'show lldp neighbors detail' output
    
    Returns list of neighbor dicts with keys:
    - remote_device: Neighbor hostname
    - remote_ip: Management IP address  
    - remote_platform: Chassis ID (used as platform identifier)
    - remote_capabilities: System capabilities
    - local_intf: Local interface
    - remote_intf: Remote interface
    - system_description: System description string
    """
    neighbors = []
    current = {}
    in_mgmt_addresses = False
    
    for line in output.splitlines():
        line_stripped = line.strip()
        
        # New neighbor entry
        if line_stripped.startswith("Chassis id:"):
            if current:
                neighbors.append(current)
                current = {}
            in_mgmt_addresses = False
            current["remote_platform"] = line_stripped.split("Chassis id:")[1].strip()
        
        # System Name (hostname)
        elif line_stripped.startswith("System Name:"):
            name = line_stripped.split("System Name:")[1].strip()
            # Strip domain if present
            current["remote_device"] = name.split('.')[0]
            in_mgmt_addresses = False
        
        # Remote interface
        elif line_stripped.startswith("Port id:"):
            current["remote_intf"] = line_stripped.split("Port id:")[1].strip()
            in_mgmt_addresses = False
        
        # Local interface
        elif line_stripped.startswith("Local Port id:"):
            current["local_intf"] = line_stripped.split("Local Port id:")[1].strip()
            in_mgmt_addresses = False
        
        # System Description (contains platform info)
        elif line_stripped.startswith("System Description:"):
            in_mgmt_addresses = False
            # Description might continue on next lines
            current["system_description"] = ""
        elif "system_description" in current and line_stripped and not line_stripped.startswith(("Time remaining", "System Capabilities", "Enabled Capabilities", "Management")):
            # Accumulate multi-line description
            if current["system_description"]:
                current["system_description"] += " "
            current["system_description"] += line_stripped
        
        # System Capabilities
        elif line_stripped.startswith("System Capabilities:"):
            caps = line_stripped.split("System Capabilities:")[1].strip()
            current["remote_capabilities"] = caps
            in_mgmt_addresses = False
        
        # Management Address section
        elif line_stripped.startswith("Management Addresses:") or line_stripped.startswith("Management Address:"):
            in_mgmt_addresses = True
        
        # IP address in management section
        elif in_mgmt_addresses and line_stripped.startswith("IP:"):
            ip_addr = line_stripped.split("IP:")[1].strip()
            if ip_addr:
                current["remote_ip"] = ip_addr
        
        # End of management addresses section
        elif line_stripped and in_mgmt_addresses:
            if not any(line_stripped.startswith(x) for x in ["IP", "IPv4", "IPv6", "Other"]):
                in_mgmt_addresses = False
    
    # Don't forget the last neighbor
    if current:
        neighbors.append(current)
    
    # Log what we extracted
    logger.info(f"Parsed {len(neighbors)} LLDP neighbors")
    for i, n in enumerate(neighbors):
        logger.debug(f"  LLDP Neighbor {i+1}: {n.get('remote_device', '?')} - IP: {n.get('remote_ip', 'MISSING')}")
    
    return neighbors


def merge_neighbor_info(cdp_neighbors: List[Dict], lldp_neighbors: List[Dict]) -> List[Dict]:
    """
    Merge CDP and LLDP neighbor information
    Prioritize CDP for platform info, but use LLDP if CDP is missing
    
    Returns: Deduplicated list of neighbors with best available info
    """
    merged = {}
    
    # Process CDP neighbors first (usually more detailed platform info)
    for neighbor in cdp_neighbors:
        key = neighbor.get('remote_device', '') or neighbor.get('remote_ip', '')
        if key:
            merged[key] = neighbor
            merged[key]['protocols'] = ['CDP']
    
    # Add or merge LLDP neighbors
    for neighbor in lldp_neighbors:
        key = neighbor.get('remote_device', '') or neighbor.get('remote_ip', '')
        if not key:
            continue
        
        if key in merged:
            # Merge: fill in missing fields from LLDP
            for field in ['remote_ip', 'remote_intf', 'local_intf']:
                if field not in merged[key] and field in neighbor:
                    merged[key][field] = neighbor[field]
            merged[key]['protocols'].append('LLDP')
            
            # Use LLDP system description if we don't have good platform info
            if 'system_description' in neighbor and neighbor['system_description']:
                merged[key]['system_description'] = neighbor['system_description']
        else:
            # New neighbor only in LLDP
            neighbor['protocols'] = ['LLDP']
            merged[key] = neighbor
    
    result = list(merged.values())
    logger.info(f"Merged to {len(result)} unique neighbors")
    return result
