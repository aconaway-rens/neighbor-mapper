# Adding Linux Server Support to Neighbor Mapper

## Required Changes

### 1. Update device_type_patterns.yaml

Add Linux device type:

```yaml
device_types:
  # ... existing Cisco types ...
  
  linux:
    platforms:
      - linux
      - ubuntu
      - debian
      - centos
      - rhel
      - fedora
    system_descriptions:
      - "Linux"
      - "Ubuntu"
      - "Debian"
      - "CentOS"
      - "Red Hat"
    priority: 80
    
# Update allowed capabilities (Linux servers show different caps)
allowed_capabilities:
  - Router
  - Switch
  - R
  - S
  - B
  - Station  # Linux servers often show as "Station"
  - Wlan
```

### 2. Add Linux LLDP Parser (parsers.py)

Add this function to parsers.py:

```python
def parse_lldpctl_output(output: str) -> List[Dict[str, str]]:
    """
    Parse 'lldpctl' output from Linux servers
    
    Returns list of neighbor dicts
    """
    neighbors = []
    current = {}
    
    for line in output.splitlines():
        line_stripped = line.strip()
        
        # New interface section
        if line_stripped.startswith("Interface:"):
            if current:
                neighbors.append(current)
                current = {}
            # Extract: "Interface:    eth0, via: LLDP, ..."
            parts = line_stripped.split(',')
            intf = parts[0].split(':')[1].strip()
            current['local_intf'] = intf
        
        # Chassis ID
        elif line_stripped.startswith("ChassisID:"):
            chassis = line_stripped.split(':', 1)[1].strip()
            current['remote_platform'] = chassis
        
        # System Name (hostname)
        elif line_stripped.startswith("SysName:"):
            name = line_stripped.split(':', 1)[1].strip()
            current['remote_device'] = name
        
        # System Description
        elif line_stripped.startswith("SysDescr:"):
            desc = line_stripped.split(':', 1)[1].strip()
            current['system_description'] = desc
            # Extract OS info for capabilities
            if 'Linux' in desc or 'Ubuntu' in desc:
                current['remote_capabilities'] = 'Station'
        
        # Management IP
        elif line_stripped.startswith("MgmtIP:"):
            ip = line_stripped.split(':', 1)[1].strip()
            current['remote_ip'] = ip
        
        # Port Description (remote interface)
        elif line_stripped.startswith("PortDescr:"):
            port = line_stripped.split(':', 1)[1].strip()
            current['remote_intf'] = port
    
    # Don't forget last neighbor
    if current:
        neighbors.append(current)
    
    logger.info(f"Parsed {len(neighbors)} LLDP neighbors from lldpctl")
    return neighbors
```

### 3. Update Discovery Logic (discovery.py)

Modify _discover_neighbors method:

```python
def _discover_neighbors(self, conn: ConnectHandler, hostname: str, device_type: str) -> List[Dict]:
    """Discover neighbors using CDP and/or LLDP"""
    cdp_neighbors = []
    lldp_neighbors = []
    
    # CDP only works on network devices
    if device_type != 'linux':
        try:
            cdp_output = conn.send_command("show cdp neighbors detail", read_timeout=30)
            cdp_neighbors = parse_cdp_neighbors_detail(cdp_output)
            logger.info(f"Found {len(cdp_neighbors)} CDP neighbors on {hostname}")
        except Exception as e:
            logger.warning(f"CDP discovery failed on {hostname}: {e}")
    
    # LLDP works on both network devices and Linux
    try:
        if device_type == 'linux':
            # Linux uses lldpctl command
            lldp_output = conn.send_command("sudo lldpctl", read_timeout=30)
            lldp_neighbors = parse_lldpctl_output(lldp_output)
        else:
            # Network devices use show lldp
            lldp_output = conn.send_command("show lldp neighbors detail", read_timeout=30)
            lldp_neighbors = parse_lldp_neighbors_detail(lldp_output)
        
        logger.info(f"Found {len(lldp_neighbors)} LLDP neighbors on {hostname}")
    except Exception as e:
        logger.warning(f"LLDP discovery failed on {hostname}: {e}")
    
    # Merge results
    merged = merge_neighbor_info(cdp_neighbors, lldp_neighbors)
    return merged
```

### 4. Update Hostname Extraction (discovery.py)

```python
def _get_hostname(self, conn: ConnectHandler, device_type: str) -> str:
    """Extract hostname from device"""
    if device_type == 'linux':
        # Linux: run hostname command
        try:
            hostname = conn.send_command("hostname").strip()
            return hostname
        except:
            # Fallback: parse from prompt (user@hostname:~$)
            prompt = conn.find_prompt()
            if '@' in prompt:
                return prompt.split('@')[1].split(':')[0]
            return "Unknown-Linux"
    else:
        # Network device: parse prompt
        prompt = conn.find_prompt()
        hostname = prompt.rstrip('#>').strip()
        return hostname
```

### 5. Update Device Type Dropdown (app.py)

Add Linux to the dropdown:

```python
DEVICE_TYPES = [
    ('cisco_ios', 'Cisco IOS'),
    ('cisco_xe', 'Cisco IOS-XE'),
    ('cisco_nxos', 'Cisco NX-OS'),
    ('cisco_xr', 'Cisco IOS-XR'),
    ('arista_eos', 'Arista EOS'),
    ('juniper_junos', 'Juniper JunOS'),
    ('linux', 'Linux/Ubuntu Server'),  # Add this
]
```

## Prerequisites on Linux Servers

Make sure LLDP daemon is installed and running:

```bash
# Install LLDP daemon
sudo apt-get install lldpd

# Enable and start
sudo systemctl enable lldpd
sudo systemctl start lldpd

# Verify it's running
sudo systemctl status lldpd

# Check neighbors (requires a few minutes to discover)
sudo lldpctl
```

## Sudo Permissions

The discovery user needs sudo access for lldpctl:

```bash
# Add to sudoers (replace 'discovery' with your username)
echo "discovery ALL=(ALL) NOPASSWD: /usr/sbin/lldpctl" | sudo tee /etc/sudoers.d/lldp
```

Or make lldpctl available without sudo:

```bash
# Create symlink in user's path
sudo ln -s /usr/sbin/lldpctl /usr/local/bin/lldpctl
sudo chmod +x /usr/sbin/lldpctl
```

## Testing

Test LLDP between two Ubuntu servers:

```bash
# On Server 1 (192.168.1.10)
sudo lldpctl

# Should show Server 2 as neighbor if connected

# On Server 2 (192.168.1.11)  
sudo lldpctl

# Should show Server 1 as neighbor
```

## Limitations

1. **No CDP Support** - Linux doesn't support CDP
2. **LLDP Only** - Can only discover LLDP-enabled neighbors
3. **Sudo Required** - lldpctl typically needs sudo
4. **Different Output** - Linux lldpctl format differs from Cisco

## Mixed Environment

The modified code can handle BOTH network devices AND Linux servers:

```
Network Topology:
    Cisco Core Switch
         |
    Cisco Dist Switch
         |
    Ubuntu Server 1 ──── Ubuntu Server 2
```

- Cisco switches: Use CDP + LLDP
- Ubuntu servers: Use LLDP only
- Cross-platform: LLDP works between Cisco and Ubuntu

## Example Use Case

**Data Center Topology:**
- Top-of-rack switches (Cisco)
- Connected to Ubuntu/Linux servers
- Map the entire infrastructure

The tool would discover:
1. Switch-to-switch connections (CDP + LLDP)
2. Switch-to-server connections (LLDP)
3. Server-to-server connections (LLDP, if networked)
