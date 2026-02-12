"""
Mock Network Simulator
Simulates network devices for testing without real hardware
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MockNetworkDevice:
    """Simulates a network device with CDP/LLDP capabilities"""
    
    # Simulated network topology - Multi-vendor environment
    MOCK_DEVICES = {
        # Core Layer - Cisco Nexus
        "192.168.1.1": {
            "hostname": "CORE-NX-01",
            "device_type": "cisco_nxos",
            "platform": "cisco Nexus9000 N9K-C93180YC-EX",
            "cdp_output": """
Device ID: DIST-EXTREME-01
Entry address(es): 
  IP address: 192.168.1.10
Platform: Extreme Summit X670-G2,  Capabilities: Router Switch 
Interface: Ethernet1/1,  Port ID (outgoing port): 1:1
Holdtime : 164 sec

Version :
ExtremeXOS version 30.7.1.4

-------------------------
Device ID: DIST-ARISTA-01
Entry address(es): 
  IP address: 192.168.1.11
Platform: Arista DCS-7280SR-48C6,  Capabilities: Router Switch 
Interface: Ethernet1/2,  Port ID (outgoing port): Ethernet1
Holdtime : 142 sec

Version :
Arista EOS version 4.28.3M

-------------------------
Device ID: FW-PALOALTO-01
Entry address(es): 
  IP address: 192.168.1.5
Platform: Palo Alto Networks PA-3220,  Capabilities: Router
Interface: Ethernet1/10,  Port ID (outgoing port): ethernet1/1
Holdtime : 155 sec

Version :
PAN-OS 10.2.3
""",
            "lldp_output": """
------------------------------------------------
Chassis id: 00:1c:73:aa:bb:cc
Port id: 1:1
Port Description: Port 1:1
System Name: DIST-EXTREME-01

System Description: 
ExtremeXOS (X670-G2) version 30.7.1.4 by release-manager

Time remaining: 112 seconds
System Capabilities: B,R
Enabled Capabilities: B,R
Management Addresses:
    IP: 192.168.1.10
Auto Negotiation - supported, enabled
Physical media capabilities:
    10GbaseT(FD)
Vlan ID: 1

Local Port id: Eth1/1

------------------------------------------------
Chassis id: 00:1c:73:dd:ee:ff
Port id: Ethernet1
Port Description: Ethernet1
System Name: DIST-ARISTA-01

System Description: 
Arista Networks EOS version 4.28.3M running on an Arista DCS-7280SR-48C6

Time remaining: 97 seconds
System Capabilities: B,R
Enabled Capabilities: B,R
Management Addresses:
    IP: 192.168.1.11
Auto Negotiation - supported, enabled
Physical media capabilities:
    10GbaseT(FD)
Vlan ID: 1

Local Port id: Eth1/2

------------------------------------------------
Chassis id: 00:1c:14:aa:bb:01
Port id: ethernet1/1
Port Description: ethernet1/1
System Name: FW-PALOALTO-01

System Description: 
Palo Alto Networks PA-3220 running PAN-OS 10.2.3

Time remaining: 105 seconds
System Capabilities: R
Enabled Capabilities: R
Management Addresses:
    IP: 192.168.1.5
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)

Local Port id: Eth1/10
"""
        },
        
        # Distribution Layer - Extreme Networks
        "192.168.1.10": {
            "hostname": "DIST-EXTREME-01",
            "device_type": "extreme",
            "platform": "Extreme Summit X670-G2",
            "cdp_output": "",
            "lldp_output": """
------------------------------------------------
Chassis id: 00:1c:73:11:22:33
Port id: Eth1/1
Port Description: Ethernet1/1
System Name: CORE-NX-01

System Description: 
Cisco Nexus Operating System (NX-OS) Software, Version 9.3(8)

Time remaining: 115 seconds
System Capabilities: B,R
Enabled Capabilities: B,R
Management Addresses:
    IP: 192.168.1.1
Auto Negotiation - supported, enabled
Physical media capabilities:
    10GbaseT(FD)
Vlan ID: 1

Local Port id: 1:1

------------------------------------------------
Chassis id: 00:0a:95:cc:dd:ee
Port id: ge-0/0/10
Port Description: ge-0/0/10
System Name: ACCESS-JUNIPER-01

System Description: 
Juniper Networks, Inc. ex4300-48p Ethernet Switch, kernel JUNOS 18.4R3.3

Time remaining: 108 seconds
System Capabilities: B,R
Enabled Capabilities: B,R
Management Addresses:
    IP: 192.168.1.20
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: 1:10

------------------------------------------------
Chassis id: 70:4c:a5:aa:bb:cc
Port id: port1
Port Description: port1
System Name: FW-FORTINET-01

System Description: 
FortiGate-100F v7.2.4,build1396,220915 (GA.F)

Time remaining: 102 seconds
System Capabilities: B,R
Enabled Capabilities: B,R
Management Addresses:
    IP: 192.168.1.6
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)

Local Port id: 1:15
"""
        },
        
        # Distribution Layer - Arista
        "192.168.1.11": {
            "hostname": "DIST-ARISTA-01",
            "device_type": "arista_eos",
            "platform": "Arista DCS-7280SR-48C6",
            "cdp_output": "",
            "lldp_output": """
------------------------------------------------
Chassis id: 00:1c:73:11:22:33
Port id: Eth1/2
Port Description: Ethernet1/2
System Name: CORE-NX-01

System Description: 
Cisco Nexus Operating System (NX-OS) Software, Version 9.3(8)

Time remaining: 108 seconds
System Capabilities: B,R
Enabled Capabilities: B,R
Management Addresses:
    IP: 192.168.1.1
Auto Negotiation - supported, enabled
Physical media capabilities:
    10GbaseT(FD)
Vlan ID: 1

Local Port id: Ethernet1

------------------------------------------------
Chassis id: 00:1c:14:bb:cc:02
Port id: ethernet1/2
Port Description: ethernet1/2
System Name: FW-PALOALTO-02

System Description: 
Palo Alto Networks PA-850 running PAN-OS 10.2.3

Time remaining: 95 seconds
System Capabilities: R
Enabled Capabilities: R
Management Addresses:
    IP: 192.168.1.7
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)

Local Port id: Ethernet10

------------------------------------------------
Chassis id: 00:50:56:aa:bb:cc
Port id: GigabitEthernet0/1
Port Description: GigabitEthernet0/1
System Name: ACCESS-CISCO-01

System Description: 
Cisco IOS Software, C2960X Software

Time remaining: 112 seconds
System Capabilities: B
Enabled Capabilities: B
Management Addresses:
    IP: 192.168.1.21
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: Ethernet20
"""
        },
        
        # Firewall - Palo Alto #1
        "192.168.1.5": {
            "hostname": "FW-PALOALTO-01",
            "device_type": "paloalto_panos",
            "platform": "Palo Alto Networks PA-3220",
            "cdp_output": "",
            "lldp_output": """
------------------------------------------------
Chassis id: 00:1c:73:11:22:33
Port id: Eth1/10
Port Description: Ethernet1/10
System Name: CORE-NX-01

System Description: 
Cisco Nexus Operating System (NX-OS) Software, Version 9.3(8)

Time remaining: 95 seconds
System Capabilities: B,R
Enabled Capabilities: B,R
Management Addresses:
    IP: 192.168.1.1
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: ethernet1/1
"""
        },
        
        # Firewall - Palo Alto #2
        "192.168.1.7": {
            "hostname": "FW-PALOALTO-02",
            "device_type": "paloalto_panos",
            "platform": "Palo Alto Networks PA-850",
            "cdp_output": "",
            "lldp_output": """
------------------------------------------------
Chassis id: 00:1c:73:dd:ee:ff
Port id: Ethernet10
Port Description: Ethernet10
System Name: DIST-ARISTA-01

System Description: 
Arista Networks EOS version 4.28.3M running on an Arista DCS-7280SR-48C6

Time remaining: 102 seconds
System Capabilities: B,R
Enabled Capabilities: B,R
Management Addresses:
    IP: 192.168.1.11
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: ethernet1/2
"""
        },
        
        # Firewall - Fortinet
        "192.168.1.6": {
            "hostname": "FW-FORTINET-01",
            "device_type": "fortinet",
            "platform": "FortiGate-100F",
            "cdp_output": "",
            "lldp_output": """
------------------------------------------------
Chassis id: 00:1c:73:aa:bb:cc
Port id: 1:15
Port Description: Port 1:15
System Name: DIST-EXTREME-01

System Description: 
ExtremeXOS (X670-G2) version 30.7.1.4 by release-manager

Time remaining: 98 seconds
System Capabilities: B,R
Enabled Capabilities: B,R
Management Addresses:
    IP: 192.168.1.10
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: port1
"""
        },
        
        # Access Layer - Juniper
        "192.168.1.20": {
            "hostname": "ACCESS-JUNIPER-01",
            "device_type": "juniper_junos",
            "platform": "Juniper EX4300-48P",
            "cdp_output": "",
            "lldp_output": """
------------------------------------------------
Chassis id: 00:1c:73:aa:bb:cc
Port id: 1:10
Port Description: Port 1:10
System Name: DIST-EXTREME-01

System Description: 
ExtremeXOS (X670-G2) version 30.7.1.4 by release-manager

Time remaining: 115 seconds
System Capabilities: B,R
Enabled Capabilities: B,R
Management Addresses:
    IP: 192.168.1.10
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: ge-0/0/10

------------------------------------------------
Chassis id: 00:1c:14:aa:bb:03
Port id: ethernet1/3
Port Description: ethernet1/3
System Name: FW-PALOALTO-03

System Description: 
Palo Alto Networks PA-440 running PAN-OS 10.2.3

Time remaining: 92 seconds
System Capabilities: R
Enabled Capabilities: R
Management Addresses:
    IP: 192.168.1.8
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)

Local Port id: ge-0/0/20
"""
        },
        
        # Access Layer - Cisco
        "192.168.1.21": {
            "hostname": "ACCESS-CISCO-01",
            "device_type": "cisco_ios",
            "platform": "cisco WS-C2960X-48",
            "cdp_output": """
Device ID: SEP001122334455
Entry address(es): 
  IP address: 192.168.1.100
Platform: Cisco IP Phone 7965,  Capabilities: Host Phone
Interface: GigabitEthernet0/5,  Port ID (outgoing port): Port 1
Holdtime : 156 sec

Version :
SCCP75.9-4-2SR3-1S

-------------------------
Device ID: AP-OFFICE-01
Entry address(es): 
  IP address: 192.168.1.50
Platform: Cisco AIR-AP3802I-B-K9,  Capabilities: Trans-Bridge
Interface: GigabitEthernet0/10,  Port ID (outgoing port): GigabitEthernet0
Holdtime : 143 sec

Version :
Cisco IOS Software, AP3800 Software (AP3G2-K9W8-M), Version 17.3.4

-------------------------
Device ID: SRV-DB-01
Entry address(es): 
  IP address: 192.168.1.200
Platform: VMware ESXi,  Capabilities: Host
Interface: GigabitEthernet0/15,  Port ID (outgoing port): eth0
Holdtime : 138 sec

Version :
Ubuntu 20.04 LTS
""",
            "lldp_output": """
------------------------------------------------
Chassis id: 00:1c:73:dd:ee:ff
Port id: Ethernet20
Port Description: Ethernet20
System Name: DIST-ARISTA-01

System Description: 
Arista Networks EOS version 4.28.3M running on an Arista DCS-7280SR-48C6

Time remaining: 105 seconds
System Capabilities: B,R
Enabled Capabilities: B,R
Management Addresses:
    IP: 192.168.1.11
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: Gi0/1
"""
        },
        
        # Firewall - Palo Alto #3 (Edge)
        "192.168.1.8": {
            "hostname": "FW-PALOALTO-03",
            "device_type": "paloalto_panos",
            "platform": "Palo Alto Networks PA-440",
            "cdp_output": "",
            "lldp_output": """
------------------------------------------------
Chassis id: 00:0a:95:cc:dd:ee
Port id: ge-0/0/20
Port Description: ge-0/0/20
System Name: ACCESS-JUNIPER-01

System Description: 
Juniper Networks, Inc. ex4300-48p Ethernet Switch, kernel JUNOS 18.4R3.3

Time remaining: 88 seconds
System Capabilities: B,R
Enabled Capabilities: B,R
Management Addresses:
    IP: 192.168.1.20
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: ethernet1/3
"""
        },
        
        # Additional Extreme Switch (Standalone for testing)
        "192.168.1.30": {
            "hostname": "EDGE-EXTREME-01",
            "device_type": "extreme",
            "platform": "Extreme Summit X460-G2",
            "cdp_output": "",
            "lldp_output": """
------------------------------------------------
Chassis id: 00:1c:73:aa:bb:cc
Port id: 1:20
Port Description: Port 1:20
System Name: DIST-EXTREME-01

System Description: 
ExtremeXOS (X670-G2) version 30.7.1.4 by release-manager

Time remaining: 110 seconds
System Capabilities: B,R
Enabled Capabilities: B,R
Management Addresses:
    IP: 192.168.1.10
Auto Negotiation - supported, enabled
Physical media capabilities:
    1000baseT(FD)
Vlan ID: 1

Local Port id: 1:1
"""
        },
        
        # Legacy devices (non-crawlable) for testing capability filtering
        "192.168.1.100": {
            "hostname": "SEP001122334455",
            "device_type": "cisco_ios",
            "platform": "Cisco IP Phone 7965",
            "cdp_output": """
Device ID: ACCESS-CISCO-01
Entry address(es): 
  IP address: 192.168.1.21
Platform: cisco WS-C2960X-48,  Capabilities: Switch IGMP 
Interface: Port 1,  Port ID (outgoing port): GigabitEthernet0/5
Holdtime : 156 sec

Version :
Cisco IOS Software, C2960X Software
""",
            "lldp_output": ""
        },
        
        "192.168.1.50": {
            "hostname": "AP-OFFICE-01",
            "device_type": "cisco_ios",
            "platform": "Cisco AIR-AP3802I-B-K9",
            "cdp_output": """
Device ID: ACCESS-CISCO-01
Entry address(es): 
  IP address: 192.168.1.21
Platform: cisco WS-C2960X-48,  Capabilities: Switch IGMP 
Interface: GigabitEthernet0,  Port ID (outgoing port): GigabitEthernet0/15
Holdtime : 148 sec

Version :
Cisco IOS Software, C2960X Software
""",
            "lldp_output": ""
        },
        
        "192.168.1.200": {
            "hostname": "SRV-DB-01",
            "device_type": "linux",
            "platform": "VMware ESXi",
            "cdp_output": """
Device ID: ACCESS-CISCO-01
Entry address(es): 
  IP address: 192.168.1.21
Platform: cisco WS-C2960X-48,  Capabilities: Switch IGMP 
Interface: eth0,  Port ID (outgoing port): GigabitEthernet0/15
Holdtime : 138 sec

Version :
Cisco IOS Software, C2960X Software
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
