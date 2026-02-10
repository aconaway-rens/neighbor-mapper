# Vendor LLDP Configuration Guide

For the neighbor-mapper to discover devices, LLDP must be enabled. Here's how to enable it on various vendors.

## 🔧 Cisco (IOS/IOS-XE)

```
! Enable LLDP globally
configure terminal
lldp run

! Enable on specific interface (optional)
interface GigabitEthernet1/0/1
 lldp transmit
 lldp receive
```

**Verify:**
```
show lldp neighbors
show lldp neighbors detail
```

## 🔧 Palo Alto Networks (PAN-OS)

LLDP is enabled by default on Palo Alto firewalls.

**Verify via CLI:**
```
show lldp neighbors all
```

**Enable/Configure via WebUI:**
1. Network → Network Profiles → Interface Mgmt
2. Check "LLDP"
3. Apply to interface profiles

**Enable via CLI (if needed):**
```
set deviceconfig system enable-lldp yes
commit
```

**Show neighbors:**
```
show lldp neighbors all
```

## 🔧 MikroTik (RouterOS)

LLDP is called "neighbor discovery" in MikroTik.

**Enable globally:**
```
/ip neighbor discovery-settings set discover-interface-list=all
```

**Enable on specific interfaces:**
```
/interface bridge port
set [find] learn=yes

/ip neighbor discovery-settings
set discover-interface-list=all
set protocol=lldp
```

**Verify:**
```
/ip neighbor print
/ip neighbor print detail
```

**Important:** For best results, ensure bridge learning is enabled:
```
/interface bridge port set [find] learn=yes
```

## 🔧 Fortinet (FortiGate)

**Enable LLDP:**
```
config system interface
    edit "port1"
        set lldp-transmission enable
        set lldp-reception enable
    next
end
```

**Enable globally on all interfaces:**
```
config system global
    set lldp-transmission enable
    set lldp-reception enable
end
```

**Verify:**
```
get system lldp neighbors
diagnose sys lldp neighbor list
```

## 🔧 Juniper (JunOS)

**Enable LLDP:**
```
set protocols lldp interface all
commit
```

**Enable on specific interface:**
```
set protocols lldp interface ge-0/0/1
commit
```

**Verify:**
```
show lldp neighbors
show lldp neighbors detail
```

## 🔧 Arista (EOS)

**Enable LLDP:**
```
configure
lldp run
```

**Verify:**
```
show lldp neighbors
show lldp neighbors detail
```

## 🔧 HPE/Aruba

### ProCurve/Comware:
```
lldp enable
```

### Aruba OS-CX:
```
lldp enable
lldp transmit
lldp receive
```

**Verify:**
```
show lldp neighbors
show lldp neighbor-info detail
```

## 🔧 Dell (OS10)

**Enable LLDP:**
```
configure terminal
lldp enable
```

**Verify:**
```
show lldp neighbors
show lldp neighbors detail
```

## 🔧 Extreme Networks

### ExtremeXOS:
```
enable lldp ports all
```

### VOSS:
```
configure terminal
lldp enable
```

**Verify:**
```
show lldp neighbors
show lldp neighbor detail
```

## 🔧 Ubiquiti

### EdgeOS:
```
configure
set service lldp interface all
commit
save
```

**Verify:**
```
show lldp neighbors
```

### UniFi (Controller):
1. Settings → Services → LLDP
2. Enable "LLDP service"

## 🔧 Barracuda CloudGen Firewall

LLDP configuration is typically done via the web interface:
1. NETWORK → Interfaces
2. Select interface
3. Enable LLDP

## 📋 General Troubleshooting

### LLDP Not Working?

**Check if enabled:**
- Most devices: `show lldp` or `show lldp status`
- Look for "LLDP: Enabled" or similar

**Check interface level:**
- LLDP might be globally enabled but disabled on specific interfaces
- Check each interface: `show lldp interface <name>`

**Timing:**
- LLDP updates every 30 seconds by default
- Wait 30-60 seconds after enabling before checking neighbors

**Firewall rules:**
- LLDP uses Ethernet type 0x88cc
- Ensure Layer 2 multicast is allowed
- Destination MAC: 01:80:C2:00:00:0E

### Discovery Not Finding Neighbors?

**For Palo Alto:**
- Check: `show lldp neighbors all`
- Ensure interfaces are in the right zone/VLAN
- Management interface might not transmit LLDP by default

**For MikroTik:**
- Verify: `/ip neighbor discovery-settings print`
- Check: `discover-interface-list` is set correctly
- Protocol should include `lldp` (not just `cdp` or `mndp`)

**For Fortinet:**
- Check each interface individually
- LLDP might be disabled on management interfaces
- Use `diagnose sys lldp neighbor list` for detailed view

## 🔍 Testing LLDP

After enabling, test from a neighbor:

**Cisco:**
```
show lldp neighbors
```

**Should see:**
```
Device ID           Local Intf     Hold-time  Capability      Port ID
PA-220              Gi1/0/1        120        R               ethernet1/1
MikroTik-Core       Gi1/0/2        120        B,R             ether1
```

If you don't see neighbors after 60 seconds, LLDP isn't working correctly.

## 💡 Pro Tips

1. **Enable everywhere** - Enable LLDP on all interfaces for best discovery
2. **Check both sides** - Both devices need LLDP enabled
3. **Wait for timers** - LLDP updates every 30s, be patient
4. **Use detail commands** - `show lldp neighbors detail` gives management IPs
5. **Check logs** - Many devices log LLDP events (new/lost neighbors)

## 🚨 Security Note

LLDP broadcasts device information (hostname, model, IP, etc.). In high-security environments:
- Only enable on trusted interfaces
- Disable on edge/user-facing ports
- Use ACLs to filter LLDP frames if needed

---

Once LLDP is enabled on your devices, the neighbor-mapper will automatically discover and map your network! 🗺️
