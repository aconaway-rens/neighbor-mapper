"""
Mock Network Simulator
Simulates network devices for testing without real hardware
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MockNetworkDevice:
    """Simulates a network device with CDP/LLDP capabilities"""
    
    # Simulated network topology
    MOCK_DEVICES = {
        "192.168.1.1": {
            "hostname": "CORE-SW-01",
            "device_type": "cisco_ios",
            "platform": "cisco WS-C4500X-32",
            "cdp_output": """
Device ID: DIST-SW-01
Entry address(es): 
  IP address: 192.168.1.10
Platform: cisco WS-C3750X-48,  Capabilities: Router Switch IGMP 
Interface: GigabitEthernet1/0/1,  Port ID (outgoing port): GigabitEthernet1/0/48
Holdtime : 164 sec

Version :
Cisco IOS Software, C3750E Software (C3750E-UNIVERSALK9-M), Version 15.2(4)E8

-------------------------
Device ID: DIST-SW-02
Entry address(es): 
  IP address: 192.168.1.11
Platform: cisco WS-C3750X-48,  Capabilities: Router Switch IGMP 
Interface: GigabitEthernet1/0/2,  Port ID (outgoing port): GigabitEthernet1/0/48
Holdtime : 142 sec

Version :
Cisco IOS Software, C3750E Software (C3750E-UNIVERSALK9-M), Version 15.2(4)E8
""",
            "lldp_output": """
------------------------------------------------
Chassis id: aabb.cc00.1122
Port id: Gi1/0/48
Port Description: GigabitEthernet1/0/48
System Name: DIST-SW-01

System Description: 
Cisco IOS Software, C3750E Software (C3750E-UNIVERSALK9-M), Version 15.2(4)E8

Time remaining: 112 seconds
System Capabilities: B,R
Enabled Capabilities: R
Management Addresses:
    IP: 192.168.1.10
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: Gi1/0/1

------------------------------------------------
Chassis id: aabb.cc00.3344
Port id: Gi1/0/48
Port Description: GigabitEthernet1/0/48
System Name: DIST-SW-02

System Description: 
Cisco IOS Software, C3750E Software (C3750E-UNIVERSALK9-M), Version 15.2(4)E8

Time remaining: 97 seconds
System Capabilities: B,R
Enabled Capabilities: R
Management Addresses:
    IP: 192.168.1.11
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: Gi1/0/2
"""
        },
        
        "192.168.1.10": {
            "hostname": "DIST-SW-01",
            "device_type": "cisco_ios",
            "platform": "cisco WS-C3750X-48",
            "cdp_output": """
Device ID: CORE-SW-01
Entry address(es): 
  IP address: 192.168.1.1
Platform: cisco WS-C4500X-32,  Capabilities: Router Switch IGMP 
Interface: GigabitEthernet1/0/48,  Port ID (outgoing port): GigabitEthernet1/0/1
Holdtime : 171 sec

Version :
Cisco IOS Software, IOS-XE Software, Catalyst 4500 L3 Switch

-------------------------
Device ID: ACCESS-SW-01
Entry address(es): 
  IP address: 192.168.1.20
Platform: cisco WS-C2960X-48,  Capabilities: Switch IGMP 
Interface: GigabitEthernet1/0/10,  Port ID (outgoing port): GigabitEthernet0/1
Holdtime : 158 sec

Version :
Cisco IOS Software, C2960X Software

-------------------------
Device ID: ACCESS-SW-02
Entry address(es): 
  IP address: 192.168.1.21
Platform: cisco WS-C2960X-48,  Capabilities: Switch IGMP 
Interface: GigabitEthernet1/0/11,  Port ID (outgoing port): GigabitEthernet0/1
Holdtime : 145 sec

Version :
Cisco IOS Software, C2960X Software

-------------------------
Device ID: SEP001122334455
Entry address(es): 
  IP address: 192.168.1.100
Platform: Cisco IP Phone 7965,  Capabilities: Host Phone 
Interface: GigabitEthernet1/0/5,  Port ID (outgoing port): Port 1
Holdtime : 132 sec

Version :
SCCP75.9-4-2SR3-1S

-------------------------
Device ID: AP-OFFICE-01
Entry address(es): 
  IP address: 192.168.1.50
Platform: Cisco AIR-AP3802I-B-K9,  Capabilities: Trans-Bridge 
Interface: GigabitEthernet1/0/15,  Port ID (outgoing port): GigabitEthernet0
Holdtime : 125 sec

Version :
Cisco IOS Software, AP3800 Software
""",
            "lldp_output": """
------------------------------------------------
Chassis id: 1122.3344.5566
Port id: Gi1/0/1
Port Description: GigabitEthernet1/0/1
System Name: CORE-SW-01

System Description: 
Cisco IOS Software, IOS-XE Software, Catalyst 4500 L3 Switch

Time remaining: 115 seconds
System Capabilities: B,R
Enabled Capabilities: R
Management Addresses:
    IP: 192.168.1.1
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: Gi1/0/48
"""
        },
        
        "192.168.1.11": {
            "hostname": "DIST-SW-02",
            "device_type": "cisco_ios",
            "platform": "cisco WS-C3750X-48",
            "cdp_output": """
Device ID: CORE-SW-01
Entry address(es): 
  IP address: 192.168.1.1
Platform: cisco WS-C4500X-32,  Capabilities: Router Switch IGMP 
Interface: GigabitEthernet1/0/48,  Port ID (outgoing port): GigabitEthernet1/0/2
Holdtime : 165 sec

Version :
Cisco IOS Software, IOS-XE Software, Catalyst 4500 L3 Switch
""",
            "lldp_output": """
------------------------------------------------
Chassis id: 1122.3344.5566
Port id: Gi1/0/2
Port Description: GigabitEthernet1/0/2
System Name: CORE-SW-01

System Description: 
Cisco IOS Software, IOS-XE Software, Catalyst 4500 L3 Switch

Time remaining: 108 seconds
System Capabilities: B,R
Enabled Capabilities: R
Management Addresses:
    IP: 192.168.1.1
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: Gi1/0/48
"""
        },
        
        "192.168.1.20": {
            "hostname": "ACCESS-SW-01",
            "device_type": "cisco_ios",
            "platform": "cisco WS-C2960X-48",
            "cdp_output": """
Device ID: DIST-SW-01
Entry address(es): 
  IP address: 192.168.1.10
Platform: cisco WS-C3750X-48,  Capabilities: Router Switch IGMP 
Interface: GigabitEthernet0/1,  Port ID (outgoing port): GigabitEthernet1/0/10
Holdtime : 152 sec

Version :
Cisco IOS Software, C3750E Software (C3750E-UNIVERSALK9-M), Version 15.2(4)E8
""",
            "lldp_output": """
------------------------------------------------
Chassis id: aabb.cc00.1122
Port id: Gi1/0/10
Port Description: GigabitEthernet1/0/10
System Name: DIST-SW-01

System Description: 
Cisco IOS Software, C3750E Software (C3750E-UNIVERSALK9-M), Version 15.2(4)E8

Time remaining: 102 seconds
System Capabilities: B,R
Enabled Capabilities: R
Management Addresses:
    IP: 192.168.1.10
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: Gi0/1
"""
        },
        
        "192.168.1.21": {
            "hostname": "ACCESS-SW-02",
            "device_type": "cisco_ios",
            "platform": "cisco WS-C2960X-48",
            "cdp_output": """
Device ID: DIST-SW-01
Entry address(es): 
  IP address: 192.168.1.10
Platform: cisco WS-C3750X-48,  Capabilities: Router Switch IGMP 
Interface: GigabitEthernet0/1,  Port ID (outgoing port): GigabitEthernet1/0/11
Holdtime : 149 sec

Version :
Cisco IOS Software, C3750E Software (C3750E-UNIVERSALK9-M), Version 15.2(4)E8
""",
            "lldp_output": ""
        },
        
        "192.168.1.100": {
            "hostname": "SEP001122334455",
            "device_type": "cisco_ios",
            "platform": "Cisco IP Phone 7965",
            "cdp_output": """
Device ID: DIST-SW-01
Entry address(es): 
  IP address: 192.168.1.10
Platform: cisco WS-C3750X-48,  Capabilities: Router Switch IGMP 
Interface: Port 1,  Port ID (outgoing port): GigabitEthernet1/0/5
Holdtime : 156 sec

Version :
Cisco IOS Software, C3750E Software (C3750E-UNIVERSALK9-M), Version 15.2(4)E8
""",
            "lldp_output": ""
        },
        
        "192.168.1.50": {
            "hostname": "AP-OFFICE-01",
            "device_type": "cisco_ios",
            "platform": "Cisco AIR-AP3802I-B-K9",
            "cdp_output": """
Device ID: DIST-SW-01
Entry address(es): 
  IP address: 192.168.1.10
Platform: cisco WS-C3750X-48,  Capabilities: Router Switch IGMP 
Interface: GigabitEthernet0,  Port ID (outgoing port): GigabitEthernet1/0/15
Holdtime : 148 sec

Version :
Cisco IOS Software, C3750E Software (C3750E-UNIVERSALK9-M), Version 15.2(4)E8
""",
            "lldp_output": ""
        }
    }
    
    def __init__(self, host: str, device_type: str, username: str, password: str):
        """Initialize mock device"""
        self.host = host
        self.device_type = device_type
        self.username = username
        self.password = password
        
        # Get device config
        if host not in self.MOCK_DEVICES:
            raise Exception(f"Mock device {host} not found. Available: {', '.join(self.MOCK_DEVICES.keys())}")
        
        self.device_config = self.MOCK_DEVICES[host]
        logger.info(f"[MOCK] Connected to {self.device_config['hostname']} ({host})")
    
    def find_prompt(self) -> str:
        """Return device prompt"""
        return f"{self.device_config['hostname']}#"
    
    def send_command(self, command: str, **kwargs) -> str:
        """Simulate command execution"""
        logger.info(f"[MOCK] Executing: {command} on {self.device_config['hostname']}")
        
        if "show cdp neighbors detail" in command:
            return self.device_config.get("cdp_output", "")
        elif "show lldp neighbors detail" in command:
            return self.device_config.get("lldp_output", "")
        else:
            return ""
    
    def disconnect(self):
        """Simulate disconnect"""
        logger.info(f"[MOCK] Disconnected from {self.device_config['hostname']}")


def is_mock_mode(host: str) -> bool:
    """Check if this IP should use mock mode"""
    return host in MockNetworkDevice.MOCK_DEVICES


def get_mock_connection(host: str, device_type: str, username: str, password: str):
    """Return a mock device connection"""
    return MockNetworkDevice(host, device_type, username, password)
