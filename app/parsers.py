"""
CDP, LLDP, and L3 Routing Protocol Neighbor Parsers
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
        elif "system_description" in current and line_stripped and not line_stripped.startswith(("Time remaining", "System Capabilities", "Enabled Capabilities", "Management", "IP:", "IPv4", "IPv6", "Auto Negotiation", "Physical media", "Vlan ID", "Local Port id")):
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
            logger.info(f"[LLDP] Found Management Addresses section")
            in_mgmt_addresses = True
        
        # IP address in management section
        elif in_mgmt_addresses and line_stripped.startswith("IP:"):
            ip_addr = line_stripped.split("IP:")[1].strip()
            logger.info(f"[LLDP] Extracting IP in mgmt section: '{ip_addr}'")
            if ip_addr:
                current["remote_ip"] = ip_addr
                logger.info(f"[LLDP] Set remote_ip = {ip_addr}")
        
        # End of management addresses section
        elif line_stripped and in_mgmt_addresses:
            if not any(line_stripped.startswith(x) for x in ["IP", "IPv4", "IPv6", "Other"]):
                logger.info(f"[LLDP] Ending mgmt section on line: {line_stripped}")
                in_mgmt_addresses = False
    
    # Don't forget the last neighbor
    if current:
        neighbors.append(current)
    
    # Log what we extracted
    logger.info(f"Parsed {len(neighbors)} LLDP neighbors")
    for i, n in enumerate(neighbors):
        logger.debug(f"  LLDP Neighbor {i+1}: {n.get('remote_device', '?')} - IP: {n.get('remote_ip', 'MISSING')}")
    
    return neighbors


def parse_ospf_neighbors(output: str) -> List[Dict]:
    """
    Parse 'show ip ospf neighbor' / 'show ip ospf neighbors' output.
    Handles Cisco IOS, IOS-XE, NX-OS tabular format.

    Returns list of neighbor dicts (only FULL state neighbors).
    """
    neighbors = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith('Neighbor') or line.startswith('OSPF') or line.startswith('Total'):
            continue
        # Tabular line: neighbor-id  pri  state  dead-time  address  interface
        parts = line.split()
        if len(parts) < 6:
            continue
        # parts[0] = neighbor ID (router ID), parts[2] = state, parts[4] = address, parts[5] = interface
        state = parts[2].upper()
        if 'FULL' not in state and 'UP' not in state:
            continue
        neighbor_id = parts[0]
        address = parts[4]
        interface = parts[5]
        # Validate that address looks like an IP
        if not _is_ip(address):
            continue
        neighbors.append({
            'remote_ip': address,
            'remote_device': None,
            'local_intf': interface,
            'remote_intf': None,
            'remote_platform': None,
            'remote_capabilities': 'Router',
            'system_description': None,
            'protocol': 'OSPF',
            'state': state,
        })
        logger.debug(f"OSPF neighbor: {neighbor_id} via {address} on {interface}")
    logger.info(f"Parsed {len(neighbors)} OSPF neighbors")
    return neighbors


def parse_eigrp_neighbors(output: str) -> List[Dict]:
    """
    Parse 'show ip eigrp neighbors' output (Cisco IOS/IOS-XE/NX-OS).

    Returns list of neighbor dicts.
    """
    neighbors = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith('H ') or line.startswith('EIGRP') or line.startswith('IP-EIGRP'):
            continue
        # Tabular line: H  address  interface  hold  uptime  srtt  rto  q  seq
        parts = line.split()
        if len(parts) < 3:
            continue
        # First column is H (index), second is address, third is interface
        try:
            int(parts[0])  # H column is a number
        except ValueError:
            continue
        address = parts[1]
        interface = parts[2]
        if not _is_ip(address):
            continue
        neighbors.append({
            'remote_ip': address,
            'remote_device': None,
            'local_intf': interface,
            'remote_intf': None,
            'remote_platform': None,
            'remote_capabilities': 'Router',
            'system_description': None,
            'protocol': 'EIGRP',
            'state': 'UP',
        })
        logger.debug(f"EIGRP neighbor: {address} on {interface}")
    logger.info(f"Parsed {len(neighbors)} EIGRP neighbors")
    return neighbors


def parse_bgp_neighbors(output: str) -> List[Dict]:
    """
    Parse 'show ip bgp neighbors' / 'show bgp ipv4 unicast neighbors' output.
    Handles Cisco IOS, IOS-XE, NX-OS, Arista multi-paragraph format.

    Returns list of neighbor dicts (only Established state).
    """
    neighbors = []
    current_ip = None
    current_state = None

    for line in output.splitlines():
        line_stripped = line.strip()

        # "BGP neighbor is X.X.X.X" or "Neighbor: X.X.X.X"
        if line_stripped.startswith('BGP neighbor is '):
            # Save previous if established
            if current_ip and current_state and 'ESTABLISHED' in current_state.upper():
                neighbors.append({
                    'remote_ip': current_ip,
                    'remote_device': None,
                    'local_intf': None,
                    'remote_intf': None,
                    'remote_platform': None,
                    'remote_capabilities': 'Router',
                    'system_description': None,
                    'protocol': 'BGP',
                    'state': current_state,
                })
            current_ip = line_stripped.split('BGP neighbor is ')[1].split(',')[0].strip()
            current_state = None

        elif line_stripped.startswith('BGP state =') or 'BGP state=' in line_stripped:
            state_part = line_stripped.replace('BGP state=', 'BGP state = ')
            current_state = state_part.split('BGP state =')[1].split(',')[0].strip()

    # Last neighbor
    if current_ip and current_state and 'ESTABLISHED' in current_state.upper():
        neighbors.append({
            'remote_ip': current_ip,
            'remote_device': None,
            'local_intf': None,
            'remote_intf': None,
            'remote_platform': None,
            'remote_capabilities': 'Router',
            'system_description': None,
            'protocol': 'BGP',
            'state': current_state,
        })

    logger.info(f"Parsed {len(neighbors)} BGP neighbors")
    return neighbors


def parse_isis_neighbors(output: str) -> List[Dict]:
    """
    Parse 'show isis neighbors' / 'show isis adjacency' output.
    Handles Cisco IOS tabular format.

    Returns list of neighbor dicts (only UP state).
    """
    neighbors = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith('System') or line.startswith('IS-IS') or line.startswith('Tag'):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        # IOS: system-id  interface  snpa  state  holdtime  type  protocol
        # Check that state field (index 3) is UP
        state = parts[3].upper() if len(parts) > 3 else ''
        if 'UP' not in state:
            continue
        system_id = parts[0]
        interface = parts[1] if len(parts) > 1 else None
        neighbors.append({
            'remote_ip': None,           # IS-IS uses system IDs, not IPs
            'remote_device': system_id,  # Use system ID as device identifier
            'local_intf': interface,
            'remote_intf': None,
            'remote_platform': None,
            'remote_capabilities': 'Router',
            'system_description': None,
            'protocol': 'IS-IS',
            'state': state,
        })
        logger.debug(f"IS-IS neighbor: {system_id} on {interface}")
    logger.info(f"Parsed {len(neighbors)} IS-IS neighbors")
    return neighbors


def parse_l3_neighbors(output: str, protocol: str) -> List[Dict]:
    """Dispatch to the correct L3 parser based on protocol name."""
    protocol = protocol.lower()
    if protocol == 'ospf':
        return parse_ospf_neighbors(output)
    elif protocol == 'eigrp':
        return parse_eigrp_neighbors(output)
    elif protocol == 'bgp':
        return parse_bgp_neighbors(output)
    elif protocol == 'isis':
        return parse_isis_neighbors(output)
    return []


def _is_ip(s: str) -> bool:
    """Return True if s looks like an IPv4 address."""
    parts = s.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def merge_neighbor_info(cdp_neighbors: List[Dict], lldp_neighbors: List[Dict],
                        l3_neighbors: Optional[List[Dict]] = None) -> List[Dict]:
    """
    Merge CDP, LLDP, and optional L3 routing protocol neighbor information.
    Prioritize CDP for platform info, but use LLDP if CDP is missing.
    L3 neighbors are deduplicated against L2 entries by IP address.

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

    # Merge L3 neighbors
    if l3_neighbors:
        # Build IP → merged-entry lookup for deduplication
        ip_index = {}
        for key, entry in merged.items():
            ip = entry.get('remote_ip')
            if ip:
                ip_index[ip] = key

        for neighbor in l3_neighbors:
            protocol = neighbor.get('protocol', 'L3')
            neighbor_ip = neighbor.get('remote_ip')
            neighbor_device = neighbor.get('remote_device')

            # Try to match against existing L2 entry by IP
            matched_key = ip_index.get(neighbor_ip) if neighbor_ip else None

            if matched_key:
                # Already known from L2 — just add the protocol
                if protocol not in merged[matched_key]['protocols']:
                    merged[matched_key]['protocols'].append(protocol)
                logger.debug(f"L3 {protocol} neighbor {neighbor_ip} merged with existing L2 entry {matched_key}")
            else:
                # L3-only neighbor — add as new entry
                key = neighbor_ip or neighbor_device
                if not key:
                    continue
                neighbor['protocols'] = [protocol]
                merged[key] = neighbor
                if neighbor_ip:
                    ip_index[neighbor_ip] = key
                logger.debug(f"L3-only {protocol} neighbor added: {key}")

    result = list(merged.values())
    logger.info(f"Merged to {len(result)} unique neighbors")
    return result
