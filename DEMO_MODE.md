# Demo Mode - Testing Without Real Network Equipment

## 🎯 Purpose

Test the neighbor-mapper application without needing actual switches or routers! The app includes a **mock network simulator** that simulates a 5-device network topology.

## 🏗️ Simulated Network Topology

```
                  CORE-SW-01
              (192.168.1.1)
                 /       \
                /         \
               /           \
        DIST-SW-01      DIST-SW-02
      (192.168.1.10)  (192.168.1.11)
           |
           |
      ┌────┴────┐
      |         |
ACCESS-SW-01  ACCESS-SW-02
(.1.20)       (.1.21)
```

**Devices:**
- CORE-SW-01: Cisco Catalyst 4500X (Core switch)
- DIST-SW-01: Cisco Catalyst 3750X (Distribution switch)
- DIST-SW-02: Cisco Catalyst 3750X (Distribution switch)
- ACCESS-SW-01: Cisco Catalyst 2960X (Access switch)
- ACCESS-SW-02: Cisco Catalyst 2960X (Access switch)

**Connections:**
- CORE-SW-01 ↔ DIST-SW-01 (CDP + LLDP)
- CORE-SW-01 ↔ DIST-SW-02 (CDP + LLDP)
- DIST-SW-01 ↔ ACCESS-SW-01 (CDP + LLDP)
- DIST-SW-01 ↔ ACCESS-SW-02 (CDP only)

## 🚀 How to Use Demo Mode

### Step 1: Start the Application

```bash
docker-compose up -d
```

### Step 2: Open Web Interface

Navigate to: **http://localhost:8000**

### Step 3: Use Demo Credentials

Enter these values in the form:

| Field | Value |
|-------|-------|
| **Seed Device IP** | `192.168.1.1` |
| **Device Type** | `Cisco IOS` |
| **Username** | `demo` (any value works) |
| **Password** | `demo` (any value works) |
| **Max Depth** | `3` |

### Step 4: Start Discovery

Click **"Start Discovery"**

### Step 5: View Results

You'll see the full topology tree:

```
CORE-SW-01 (192.168.1.1)
├─[CDP+LLDP] Gi1/0/1 ↔ Gi1/0/48 (192.168.1.10)
│   DIST-SW-01 (192.168.1.10)
│   ├─[CDP+LLDP] Gi1/0/10 ↔ Gi0/1 (192.168.1.20)
│   │   ACCESS-SW-01 (192.168.1.20)
│   └─[CDP] Gi1/0/11 ↔ Gi0/1 (192.168.1.21)
│       ACCESS-SW-02 (192.168.1.21)
└─[CDP+LLDP] Gi1/0/2 ↔ Gi1/0/48 (192.168.1.11)
    DIST-SW-02 (192.168.1.11)
```

## 🎮 Try Different Scenarios

### Scenario 1: Start from Distribution Switch
- **Seed IP:** `192.168.1.10`
- **Device Type:** `Cisco IOS`
- **Max Depth:** `2`

**Expected:** Discovers CORE-SW-01 (upstream) and ACCESS switches (downstream)

### Scenario 2: Start from Access Switch
- **Seed IP:** `192.168.1.20`
- **Device Type:** `Cisco IOS`
- **Max Depth:** `2`

**Expected:** Discovers only DIST-SW-01 (single connection)

### Scenario 3: Limited Depth
- **Seed IP:** `192.168.1.1`
- **Max Depth:** `1`

**Expected:** Only immediate neighbors (DIST-SW-01 and DIST-SW-02)

## 📊 What Gets Tested

✅ **CDP Parsing** - All devices have CDP neighbors
✅ **LLDP Parsing** - Most devices have LLDP neighbors
✅ **Protocol Merging** - Shows CDP+LLDP when both present
✅ **Recursive Discovery** - Crawls multiple hops
✅ **Interface Mapping** - Shows local ↔ remote interfaces
✅ **IP Display** - Management IPs shown
✅ **Device Type Detection** - Different Cisco platforms
✅ **Depth Limiting** - Respects max_depth setting
✅ **Loop Prevention** - Won't revisit devices

## 🔍 How Mock Mode Works

The app automatically detects if you're using a demo IP address:

**Mock IPs:**
- 192.168.1.1 → CORE-SW-01
- 192.168.1.10 → DIST-SW-01
- 192.168.1.11 → DIST-SW-02
- 192.168.1.20 → ACCESS-SW-01
- 192.168.1.21 → ACCESS-SW-02

**Any other IP** → Tries real SSH connection

## 🎯 Use Cases

### 1. Demo/Presentation
Show the tool to others without network access

### 2. Development Testing
Test code changes without hardware

### 3. UI Testing
Verify web interface works correctly

### 4. Training
Learn how the tool works before using on real network

### 5. CI/CD Testing
Run automated tests in build pipeline

## 🔄 Switching Between Mock and Real

**Mock Mode:**
- Use IPs: 192.168.1.1, .10, .11, .20, .21
- No actual network needed
- Instant responses

**Real Mode:**
- Use any other IP address
- Requires actual network devices
- Real SSH connections

## 🛠️ Customizing Mock Network

To add or modify mock devices, edit `app/mock_devices.py`:

```python
MOCK_DEVICES = {
    "192.168.1.1": {
        "hostname": "CORE-SW-01",
        "device_type": "cisco_ios",
        "platform": "cisco WS-C4500X-32",
        "cdp_output": """...""",
        "lldp_output": """..."""
    },
    # Add more devices here
}
```

## 📝 Mock Device Details

### CORE-SW-01 (192.168.1.1)
- **Platform:** Cisco Catalyst 4500X
- **Neighbors:** 2 (DIST-SW-01, DIST-SW-02)
- **Protocols:** CDP + LLDP

### DIST-SW-01 (192.168.1.10)
- **Platform:** Cisco Catalyst 3750X
- **Neighbors:** 3 (CORE-SW-01, ACCESS-SW-01, ACCESS-SW-02)
- **Protocols:** CDP + LLDP

### DIST-SW-02 (192.168.1.11)
- **Platform:** Cisco Catalyst 3750X
- **Neighbors:** 1 (CORE-SW-01)
- **Protocols:** CDP + LLDP

### ACCESS-SW-01 (192.168.1.20)
- **Platform:** Cisco Catalyst 2960X
- **Neighbors:** 1 (DIST-SW-01)
- **Protocols:** CDP + LLDP

### ACCESS-SW-02 (192.168.1.21)
- **Platform:** Cisco Catalyst 2960X
- **Neighbors:** 1 (DIST-SW-01)
- **Protocols:** CDP only

## ⚡ Quick Test Commands

```bash
# Start app
docker-compose up -d

# Open browser
open http://localhost:8000

# Use these credentials for demo:
# IP: 192.168.1.1
# Type: Cisco IOS
# User: demo
# Pass: demo

# View logs
docker-compose logs -f

# Look for [MOCK] indicators in logs
```

## 🎓 Learning Objectives

Use demo mode to understand:

1. **Discovery Process** - How the tool crawls the network
2. **Protocol Differences** - CDP vs LLDP output
3. **Topology Visualization** - ASCII tree representation
4. **Interface Mapping** - Local/remote interface connections
5. **Recursive Discovery** - Multi-hop neighbor discovery
6. **Depth Control** - How max_depth affects scope

## 📌 Important Notes

- Mock mode requires **no network access**
- Mock mode requires **no SSH credentials** (any value works)
- Mock responses are **instant** (no timeouts)
- Mock devices have **realistic CDP/LLDP output**
- Mock mode is **automatically detected** by IP address

## 🚫 Limitations

- Fixed topology (5 devices)
- No dynamic changes
- Can't modify device configs
- All devices are Cisco (no multi-vendor)

## 🎉 Perfect For

✅ Demonstrations
✅ Screenshots/videos
✅ Training sessions
✅ Development testing
✅ CI/CD pipelines
✅ Learning the tool
✅ Verifying changes

## 🔜 Next Steps

After testing with demo mode:

1. **Try on real network** - Use actual device IPs
2. **Add device patterns** - Edit YAML for your devices
3. **Customize** - Modify templates, add features
4. **Deploy** - Use in production environment

---

**Demo mode makes it easy to test and demonstrate the neighbor-mapper without any network infrastructure!** 🎊
