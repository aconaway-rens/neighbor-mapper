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
            "arp_output": """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.1         -       aabb.cc00.0101  ARPA   mgmt0
Internet  192.168.1.10        3       aabb.cc00.0110  ARPA   Ethernet1/1
Internet  192.168.1.11        5       aabb.cc00.0111  ARPA   Ethernet1/2
Internet  192.168.1.5         2       aabb.cc00.0105  ARPA   Ethernet1/10
Internet  10.0.0.1            1       aabb.cc00.0001  ARPA   Ethernet1/20
Internet  10.0.0.2            4       aabb.cc00.0002  ARPA   Ethernet1/20
Internet  10.0.0.3            0       aabb.cc00.0003  ARPA   Ethernet1/20
""",
            "ospf_output": """OSPF Process ID 1 VRF default
Total number of neighbors: 2

Neighbor ID     Pri   State           Dead Time   Address         Interface
192.168.1.10      1   FULL/DR         00:00:39    192.168.1.10    Eth1/1
192.168.1.11      1   FULL/BDR        00:00:37    192.168.1.11    Eth1/2
""",
            "bgp_output": """
BGP neighbor is 10.0.0.1,  remote AS 65001, ebgp link,  Peer index 1
  BGP version 4, remote router ID 10.0.0.1
  BGP state = Established, up for 2d17h
  Last read 00:00:43, Last write 00:00:19
  Hold time is 180, keepalive interval is 60 seconds
  Configured hold time is 180, keepalive interval is 60 seconds
  Local host: 192.168.1.1, Local port: 179
  Foreign host: 10.0.0.1, Foreign port: 63042
""",
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
            "arp_output": """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.10        -       aabb.cc00.0110  ARPA   vlan10
Internet  192.168.1.1         2       aabb.cc00.0101  ARPA   1:1
Internet  192.168.1.20        1       aabb.cc00.0120  ARPA   1:10
Internet  192.168.1.6         3       aabb.cc00.0106  ARPA   1:15
Internet  10.10.1.1           0       aabb.cc10.0101  ARPA   vlan100
Internet  10.10.1.10          2       aabb.cc10.0110  ARPA   vlan100
Internet  10.10.1.20          5       aabb.cc10.0120  ARPA   vlan100
Internet  10.10.1.30          1       aabb.cc10.0130  ARPA   vlan100
Internet  10.10.1.40          4       aabb.cc10.0140  ARPA   vlan100
Internet  10.10.2.1           0       aabb.cc10.0201  ARPA   vlan200
Internet  10.10.2.10          2       aabb.cc10.0210  ARPA   vlan200
""",
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
            "arp_output": """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.11        -       aabb.cc00.0111  ARPA   Management1
Internet  192.168.1.1         1       aabb.cc00.0101  ARPA   Ethernet1
Internet  192.168.1.7         2       aabb.cc00.0107  ARPA   Ethernet10
Internet  192.168.1.21        3       aabb.cc00.0121  ARPA   Ethernet20
Internet  10.20.1.1           0       aabb.cc20.0101  ARPA   Vlan20
Internet  10.20.1.11          1       aabb.cc20.0111  ARPA   Vlan20
Internet  10.20.1.21          4       aabb.cc20.0121  ARPA   Vlan20
Internet  10.20.1.31          2       aabb.cc20.0131  ARPA   Vlan20
Internet  10.20.2.1           0       aabb.cc20.0201  ARPA   Vlan30
Internet  10.20.2.11          3       aabb.cc20.0211  ARPA   Vlan30
""",
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
            "arp_output": """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.5         -       aabb.cc00.0105  ARPA   ethernet1/1
Internet  192.168.1.1         1       aabb.cc00.0101  ARPA   ethernet1/1
Internet  172.16.0.1          0       aabb.cc16.0001  ARPA   ethernet1/2
Internet  172.16.0.10         3       aabb.cc16.0010  ARPA   ethernet1/2
Internet  172.16.0.20         5       aabb.cc16.0020  ARPA   ethernet1/2
""",
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
            "arp_output": """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.7         -       aabb.cc00.0107  ARPA   ethernet1/2
Internet  192.168.1.11        2       aabb.cc00.0111  ARPA   ethernet1/2
Internet  10.30.0.1           0       aabb.cc30.0001  ARPA   ethernet1/1
Internet  10.30.0.10          1       aabb.cc30.0010  ARPA   ethernet1/1
Internet  10.30.0.20          3       aabb.cc30.0020  ARPA   ethernet1/1
""",
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
            "arp_output": """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.6         -       aabb.cc00.0106  ARPA   port1
Internet  192.168.1.10        2       aabb.cc00.0110  ARPA   port1
Internet  10.40.0.1           0       aabb.cc40.0001  ARPA   port2
Internet  10.40.0.10          3       aabb.cc40.0010  ARPA   port2
Internet  10.40.0.20          1       aabb.cc40.0020  ARPA   port2
""",
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
            "arp_output": """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.20        -       aabb.cc00.0120  ARPA   me0
Internet  192.168.1.10        1       aabb.cc00.0110  ARPA   ge-0/0/10
Internet  10.50.1.1           0       aabb.cc50.0101  ARPA   vlan.50
Internet  10.50.1.10          2       aabb.cc50.0110  ARPA   vlan.50
Internet  10.50.1.20          4       aabb.cc50.0120  ARPA   vlan.50
Internet  10.50.1.30          1       aabb.cc50.0130  ARPA   vlan.50
Internet  10.50.1.40          3       aabb.cc50.0140  ARPA   vlan.50
Internet  10.50.1.50          0       aabb.cc50.0150  ARPA   vlan.50
Internet  10.50.1.60          2       aabb.cc50.0160  ARPA   vlan.50
""",
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
            "arp_output": """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.21        -       aabb.cc00.0121  ARPA   Vlan1
Internet  192.168.1.11        1       aabb.cc00.0111  ARPA   GigabitEthernet0/1
Internet  192.168.1.100       0       aabb.cc01.0100  ARPA   GigabitEthernet0/5
Internet  192.168.1.50        2       aabb.cc01.0050  ARPA   GigabitEthernet0/10
Internet  192.168.1.200       1       aabb.cc01.0200  ARPA   GigabitEthernet0/15
Internet  192.168.1.201       3       aabb.cc01.0201  ARPA   GigabitEthernet0/16
Internet  192.168.1.202       0       aabb.cc01.0202  ARPA   GigabitEthernet0/17
Internet  192.168.1.203       4       aabb.cc01.0203  ARPA   GigabitEthernet0/18
Internet  192.168.1.204       2       aabb.cc01.0204  ARPA   GigabitEthernet0/19
Internet  192.168.1.205       1       aabb.cc01.0205  ARPA   GigabitEthernet0/20
""",
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
            "arp_output": """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.8         -       aabb.cc00.0108  ARPA   ethernet1/3
Internet  192.168.1.20        1       aabb.cc00.0120  ARPA   ethernet1/3
Internet  10.70.0.1           0       aabb.cc70.0001  ARPA   ethernet1/1
Internet  10.70.0.10          2       aabb.cc70.0010  ARPA   ethernet1/1
""",
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
            "arp_output": """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.1.30        -       aabb.cc00.0130  ARPA   vlan1
Internet  192.168.1.10        1       aabb.cc00.0110  ARPA   1:1
Internet  10.60.1.1           0       aabb.cc60.0101  ARPA   vlan60
Internet  10.60.1.10          2       aabb.cc60.0110  ARPA   vlan60
Internet  10.60.1.20          3       aabb.cc60.0120  ARPA   vlan60
""",
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
        },

        # L3-only WAN router — no CDP/LLDP, only reachable via BGP from CORE-NX-01
        "10.0.0.1": {
            "hostname": "WAN-ROUTER-01",
            "device_type": "cisco_ios",
            "platform": "Cisco ISR4451-X/K9",
            "cdp_output": "",
            "lldp_output": "",
            "arp_output": """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  10.0.0.1            -       aabb.cc00.0001  ARPA   GigabitEthernet0/0
Internet  192.168.1.1         2       aabb.cc00.0101  ARPA   GigabitEthernet0/0
Internet  10.0.0.10           0       aabb.cc00.0010  ARPA   GigabitEthernet0/1
Internet  10.0.0.20           1       aabb.cc00.0020  ARPA   GigabitEthernet0/1
Internet  10.0.0.30           4       aabb.cc00.0030  ARPA   GigabitEthernet0/1
""",
            "bgp_output": """
BGP neighbor is 192.168.1.1,  remote AS 65000, ebgp link,  Peer index 1
  BGP version 4, remote router ID 192.168.1.1
  BGP state = Established, up for 2d17h
  Last read 00:00:43, Last write 00:00:19
  Hold time is 180, keepalive interval is 60 seconds
  Local host: 10.0.0.1, Local port: 179
  Foreign host: 192.168.1.1, Foreign port: 63042
""",
            "ospf_output": "",
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
        elif "ospf neighbor" in command or "ospf neighbors" in command or "ospf adjacency" in command:
            return self.device_config.get("ospf_output", "")
        elif "eigrp neighbor" in command or "eigrp neighbors" in command:
            return self.device_config.get("eigrp_output", "")
        elif "bgp neighbor" in command or "bgp neighbors" in command or "bgp ipv4 unicast neighbor" in command:
            return self.device_config.get("bgp_output", "")
        elif "isis neighbor" in command or "isis adjacency" in command:
            return self.device_config.get("isis_output", "")
        elif "show ip arp" in command or "show arp" in command or "show iparp" in command:
            return self.device_config.get("arp_output", "")
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
