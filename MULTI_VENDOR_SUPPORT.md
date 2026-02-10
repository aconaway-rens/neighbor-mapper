# Multi-Vendor Support

The neighbor-mapper now supports network devices from multiple vendors!

## 🌐 Supported Vendors

### Cisco
- **IOS** - Traditional Cisco IOS (2960, 3750, ISR routers)
- **IOS-XE** - Modern Cisco platforms (Cat 9K, ISR 4K, ASR 1K)
- **NX-OS** - Nexus data center switches (3K, 5K, 7K, 9K)
- **IOS-XR** - Service provider routers (ASR 9K, NCS)

### Arista
- **EOS** - All Arista switches running EOS

### Juniper
- **JunOS** - EX, QFX, MX, SRX series

### Fortinet
- **FortiGate** - FortiGate firewalls and FortiSwitch
- Netmiko device type: `fortinet`

### HPE/HP
- **ProCurve** - HP 2530, 2920, 2930, 5400 series
- **Comware** - HPE 5130, 5900, 12500 series
- **Aruba OS-CX** - Aruba 6300, 8320, 8400 series

### Dell
- **OS10** - Dell PowerSwitch S4048, S5048, S6000, Z9100
- **Force10** - Older Force10 FTOS devices

### Extreme Networks
- **ExtremeXOS** - Summit X440, X450, X460, X670, X870
- **VOSS** - VSP series (Virtual Services Platform)

### Ubiquiti
- **EdgeOS** - EdgeRouter, EdgeSwitch, EdgeMax
- **UniFi** - UniFi switches (limited LLDP support)

### Palo Alto Networks
- **PAN-OS** - All Palo Alto firewalls (PA-220, PA-440, PA-850, PA-3000, PA-5000, PA-7000 series)
- Netmiko device type: `paloalto_panos`

### MikroTik
- **RouterOS** - All MikroTik routers and switches (RouterBoard, CRS, CCR, hEX series)
- Netmiko device type: `mikrotik_routeros`

### Barracuda
- **CloudGen Firewall** - Barracuda firewall appliances

## 📋 Protocol Support by Vendor

| Vendor | CDP | LLDP | Notes |
|--------|-----|------|-------|
| Cisco | ✅ | ✅ | Full support for both |
| Arista | ❌ | ✅ | LLDP only |
| Juniper | ❌ | ✅ | LLDP only |
| Palo Alto | ❌ | ✅ | LLDP only |
| MikroTik | ❌ | ✅ | LLDP only (enable with `/interface bridge port set [find] learn=yes`) |
| Fortinet | ❌ | ✅ | LLDP only |
| HPE/HP | ❌ | ✅ | LLDP only |
| Dell | ❌ | ✅ | LLDP only |
| Extreme | ❌ | ✅ | LLDP only |
| Ubiquiti | ❌ | ⚠️ | Limited LLDP |
| Barracuda | ❌ | ✅ | LLDP only |

**Note:** CDP is a Cisco proprietary protocol. Non-Cisco vendors use LLDP (IEEE 802.1AB standard).

## 🔧 Configuration

All vendor patterns are defined in `config/device_type_patterns.yaml`. You can easily add or modify patterns without changing code!

### Example: Adding a New Dell Model

```yaml
dell_os10:
  platforms:
    - dell
    - s4048
    - s5048
    - s6000
    - s6010
    - z9100
    - powerswitch
    - dell emc
    - s3048  # Add your new model here!
  system_descriptions:
    - "Dell EMC"
    - "Dell Networking OS10"
    - "OS10"
  priority: 82
```

## 🎯 Device Type Detection

The app automatically detects device types based on:

1. **Platform string** from CDP (Cisco only)
2. **System description** from LLDP (all vendors)
3. **Capability flags** (Router, Switch, etc.)

### Detection Examples

**Fortinet FortiGate:**
```
System Description: Fortinet FortiGate-600D v6.4.8
Platform: FortiGate-600D
→ Detected as: fortinet
```

**HPE Aruba:**
```
System Description: ArubaOS-CX FL.10.08.1010
Platform: Aruba JL635A
→ Detected as: aruba_os
```

**Dell OS10:**
```
System Description: Dell Networking OS10
Platform: Dell EMC Networking S4048-ON
→ Detected as: dell_os10
```

**Ubiquiti EdgeSwitch:**
```
System Description: EdgeSwitch 48 750W, 1.8.2
Platform: EdgeSwitch
→ Detected as: ubiquiti_edge
```

**Palo Alto Firewall:**
```
System Description: Palo Alto Networks PA-220 running PAN-OS 10.1.0
Platform: PA-220
→ Detected as: paloalto_panos
```

**MikroTik Router:**
```
System Description: MikroTik RouterOS 7.6
Platform: MikroTik RB5009
→ Detected as: mikrotik_routeros
```

## ⚙️ Using Multi-Vendor Networks

### Example: Mixed Cisco/Arista Network

```
Cisco Core Switch (seed)
  ├─ Cisco Distribution (detected: cisco_ios)
  ├─ Arista ToR Switch (detected: arista_eos)
  └─ Fortinet Firewall (detected: fortinet)
```

The app will:
1. Connect to Cisco core using `cisco_ios`
2. Parse CDP from Cisco neighbors
3. Parse LLDP from all neighbors
4. Detect Arista as `arista_eos` from LLDP system description
5. Connect to Arista using correct device type
6. Continue discovery recursively

### Example: HPE/Aruba Campus

```
HPE Comware Core (seed)
  ├─ Aruba OS-CX Distribution
  │   ├─ Aruba Access Switch
  │   └─ HP ProCurve Access
  └─ Fortinet Firewall
```

## 🔍 Troubleshooting Multi-Vendor

### Device Not Detected Correctly?

**Check the logs:**
```
[INFO] Neighbor: ARUBA-DIST-01 - Type: aruba_os - Caps: Bridge Router
```

If `Type: None`, the pattern didn't match.

**Solution:** Add the platform string to YAML:
```yaml
aruba_os:
  platforms:
    - aruba
    - arubaos-cx
    - your-platform-string-here  # Add this
```

### Connection Fails?

**Wrong Netmiko device type?** Check Netmiko's supported platforms:
- Fortinet: `fortinet`
- HPE: `hp_procurve` or `hp_comware`
- Aruba: `aruba_os`
- Dell: `dell_os10` or `dell_force10`
- Extreme: `extreme` or `extreme_vsp`
- Ubiquiti: `ubiquiti_edgerouter` or `ubiquiti_edgeswitch`

Update the YAML if needed!

## 📝 Adding a New Vendor

To add support for a new vendor:

### 1. Add to YAML config

```yaml
# config/device_type_patterns.yaml
new_vendor:
  platforms:
    - vendor-model-123
    - vendor-model-456
  system_descriptions:
    - "Vendor OS"
    - "Vendor Name"
  priority: 75
```

### 2. Add to dropdown (optional)

```python
# app/app.py
DEVICE_TYPES = [
    # ... existing types ...
    ('new_vendor', 'New Vendor Name'),
]
```

### 3. Test!

Run discovery and check logs to verify detection works.

## 🎓 Best Practices

1. **Start with one device** - Test with a single vendor before full discovery
2. **Check LLDP is enabled** - Non-Cisco vendors need LLDP
3. **Verify credentials** - Some vendors need different privilege levels
4. **Monitor logs** - Watch for detection and connection issues
5. **Update patterns** - Add your specific models to YAML

## 🌟 Coming Soon

Potential future vendor support:
- Palo Alto Networks firewalls
- Checkpoint firewalls
- Mikrotik RouterOS
- VyOS/Vyatta
- Cumulus Linux
- SONiC

Want to add a vendor? Just update the YAML file! 🚀
