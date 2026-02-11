# Multi-Vendor Demo Topology

## Overview

The mock devices have been updated to provide a realistic multi-vendor network environment for testing the neighbor mapper application. This topology includes devices from **Cisco, Extreme Networks, Palo Alto Networks, Fortinet, Arista, and Juniper**.

## Network Topology

```
                    CORE-NX-01 (Cisco Nexus)
                    192.168.1.1
                          |
        +----------------+------------------+------------------+
        |                |                  |                  |
   DIST-EXTREME-01  DIST-ARISTA-01   FW-PALOALTO-01    
   192.168.1.10     192.168.1.11     192.168.1.5        
   (Extreme X670)   (Arista DCS)     (PA-3220)          
        |                |                                     
        |                +---------------+                     
        |                                |                     
   +----+----+                      ACCESS-CISCO-01            
   |         |                      192.168.1.21               
ACCESS-    FW-FORTINET-01           (Cisco 2960X)              
JUNIPER-01 192.168.1.6                                         
192.168.1.20 (FortiGate-100F)                                  
(Juniper                                                       
EX4300)                                                        
   |                                                           
   |                                                           
FW-PALOALTO-03                                                 
192.168.1.8                                                    
(PA-440)                                                       
```

## Device Inventory

### Core Layer
| IP Address    | Hostname       | Vendor | Platform                    | Device Type    |
|---------------|----------------|--------|-----------------------------|----------------|
| 192.168.1.1   | CORE-NX-01     | Cisco  | Nexus9000 N9K-C93180YC-EX   | cisco_nxos     |

### Distribution Layer
| IP Address    | Hostname           | Vendor           | Platform                  | Device Type      |
|---------------|--------------------|------------------|---------------------------|------------------|
| 192.168.1.10  | DIST-EXTREME-01    | Extreme Networks | Summit X670-G2            | extreme          |
| 192.168.1.11  | DIST-ARISTA-01     | Arista           | DCS-7280SR-48C6           | arista_eos       |

### Firewall Layer
| IP Address    | Hostname           | Vendor                | Platform          | Device Type       |
|---------------|--------------------|-----------------------|-------------------|-------------------|
| 192.168.1.5   | FW-PALOALTO-01     | Palo Alto Networks    | PA-3220           | paloalto_panos    |
| 192.168.1.6   | FW-FORTINET-01     | Fortinet              | FortiGate-100F    | fortinet          |
| 192.168.1.7   | FW-PALOALTO-02     | Palo Alto Networks    | PA-850            | paloalto_panos    |
| 192.168.1.8   | FW-PALOALTO-03     | Palo Alto Networks    | PA-440            | paloalto_panos    |

### Access Layer
| IP Address    | Hostname           | Vendor    | Platform          | Device Type      |
|---------------|--------------------|-----------|-------------------|------------------|
| 192.168.1.20  | ACCESS-JUNIPER-01  | Juniper   | EX4300-48P        | juniper_junos    |
| 192.168.1.21  | ACCESS-CISCO-01    | Cisco     | WS-C2960X-48      | cisco_ios        |
| 192.168.1.30  | EDGE-EXTREME-01    | Extreme   | Summit X460-G2    | extreme          |

### End Devices (Non-Crawlable)
| IP Address    | Hostname            | Type               |
|---------------|---------------------|--------------------|
| 192.168.1.100 | SEP001122334455     | Cisco IP Phone     |
| 192.168.1.50  | AP-OFFICE-01        | Cisco Access Point |

## Testing Instructions

### Quick Test - Start from Core
```bash
# Start the application
docker-compose up -d

# Open browser to http://localhost:8000

# Enter these details:
Device IP: 192.168.1.1
Device Type: cisco_nxos (auto-detected from "cisco_ios" is fine too)
Username: demo
Password: demo
Discovery Depth: 3
```

### Test Different Entry Points

#### Test Extreme Networks Detection
```
Device IP: 192.168.1.10
Device Type: extreme
Username: demo
Password: demo
```

#### Test Palo Alto Networks Detection
```
Device IP: 192.168.1.5
Device Type: paloalto_panos
Username: demo
Password: demo
```

#### Test Fortinet Detection
```
Device IP: 192.168.1.6
Device Type: fortinet
Username: demo
Password: demo
```

#### Test Arista Detection
```
Device IP: 192.168.1.11
Device Type: arista_eos
Username: demo
Password: demo
```

#### Test Juniper Detection
```
Device IP: 192.168.1.20
Device Type: juniper_junos
Username: demo
Password: demo
```

## Expected Output

When starting from CORE-NX-01 (192.168.1.1) with depth 3, you should see:

```
CORE-NX-01 (192.168.1.1)
├─[LLDP] Eth1/1 ↔ 1:1 (192.168.1.10)
│   DIST-EXTREME-01 (192.168.1.10)
│   ├─[LLDP] 1:10 ↔ ge-0/0/10 (192.168.1.20)
│   │   ACCESS-JUNIPER-01 (192.168.1.20)
│   │   └─[LLDP] ge-0/0/20 ↔ ethernet1/3 (192.168.1.8)
│   │       FW-PALOALTO-03 (192.168.1.8)
│   └─[LLDP] 1:15 ↔ port1 (192.168.1.6)
│       FW-FORTINET-01 (192.168.1.6)
├─[LLDP] Eth1/2 ↔ Ethernet1 (192.168.1.11)
│   DIST-ARISTA-01 (192.168.1.11)
│   ├─[LLDP] Ethernet10 ↔ ethernet1/2 (192.168.1.7)
│   │   FW-PALOALTO-02 (192.168.1.7)
│   └─[LLDP] Ethernet20 ↔ Gi0/1 (192.168.1.21)
│       ACCESS-CISCO-01 (192.168.1.21)
└─[LLDP] Eth1/10 ↔ ethernet1/1 (192.168.1.5)
    FW-PALOALTO-01 (192.168.1.5)
```

## Key Features Demonstrated

### 1. Multi-Vendor Support
- **Cisco**: Nexus (NX-OS), Catalyst (IOS)
- **Extreme Networks**: Summit switches (ExtremeXOS)
- **Palo Alto Networks**: PA-Series firewalls (PAN-OS)
- **Fortinet**: FortiGate firewalls (FortiOS)
- **Arista**: DCS switches (EOS)
- **Juniper**: EX switches (JunOS)

### 2. LLDP-Only Discovery
All non-Cisco devices use LLDP exclusively, which is more common in multi-vendor environments. This tests the LLDP parsing capabilities thoroughly.

### 3. Device Type Auto-Detection
The platform strings are designed to trigger the correct device type detection based on patterns in `config/device_type_patterns.yaml`.

### 4. Capability Filtering
The firewalls report as Routers (R), while switches report as Bridges/Switches (B/S/R), demonstrating the capability-based crawling logic.

### 5. Interface Naming Conventions
Different vendors use different interface naming:
- **Cisco**: GigabitEthernet, Ethernet
- **Extreme**: Port 1:1, 1:10 format
- **Palo Alto**: ethernet1/1 format
- **Fortinet**: port1 format
- **Arista**: Ethernet1 format
- **Juniper**: ge-0/0/10 format

### 6. End Device Filtering
The IP Phone and Access Point are included but should not be crawled (they report capabilities of "Host Phone" and "Trans-Bridge").

## Protocol Coverage

### CDP Support
- Only Cisco core device (CORE-NX-01) has CDP enabled
- Tests CDP output parsing

### LLDP Support
- All devices support LLDP (industry standard)
- Primary protocol for multi-vendor environments
- Tests LLDP output parsing across different vendor formats

## Validation Points

Test that the application correctly:

1. ✅ Detects Extreme Networks devices from LLDP system description
2. ✅ Detects Palo Alto Networks devices from platform strings
3. ✅ Detects Fortinet devices from platform strings
4. ✅ Detects Arista devices from platform strings
5. ✅ Detects Juniper devices from platform strings
6. ✅ Parses different interface naming conventions
7. ✅ Filters non-crawlable devices (phones, APs)
8. ✅ Handles LLDP-only environments
9. ✅ Correctly maps interface connections across vendors
10. ✅ Displays management IP addresses

## Troubleshooting

### Device Not Detected Correctly

Check `logs/app.log` for device type detection results. The log will show:
```
Detected device type: extreme for platform: Extreme Summit X670-G2
```

If detection fails, verify that the platform string matches patterns in `config/device_type_patterns.yaml`.

### Missing Neighbors

Ensure you're looking at the right protocol:
- Cisco devices may use CDP or LLDP
- Non-Cisco devices typically use LLDP only

### Depth Limitations

Some paths are 3+ hops deep. Use depth=3 or higher to see the full topology.

## Adding More Demo Devices

To add additional demo devices, edit `app/mock_devices.py`:

```python
"192.168.1.XX": {
    "hostname": "DEVICE-NAME",
    "device_type": "netmiko_device_type",
    "platform": "vendor platform string",
    "cdp_output": "...",
    "lldp_output": "..."
}
```

Then update the LLDP/CDP outputs of neighboring devices to include the new device.

## Production Use

For production environments:
1. Disable demo mode by using real device IPs
2. Ensure real credentials are provided
3. Verify network connectivity to all devices
4. Check that SSH is enabled and accessible
5. Confirm CDP/LLDP is running on devices

The same patterns and detection logic will work with real devices!
