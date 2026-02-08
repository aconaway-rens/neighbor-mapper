# System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                            │
│                     http://localhost:8000                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER CONTAINER                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Flask Web App                          │  │
│  │                     (app.py)                              │  │
│  │  • Handles HTTP requests                                 │  │
│  │  • Renders HTML template                                 │  │
│  │  • Orchestrates discovery                                │  │
│  └────────────┬──────────────────────────────────────────────┘  │
│               │                                                  │
│               ▼                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │             Topology Discoverer                           │  │
│  │              (discovery.py)                               │  │
│  │  • SSH connection management                             │  │
│  │  • Recursive discovery queue                             │  │
│  │  • Loop prevention                                        │  │
│  └────┬───────────────────────┬──────────────────────────────┘  │
│       │                       │                                  │
│       ▼                       ▼                                  │
│  ┌─────────────┐      ┌─────────────────┐                       │
│  │  Parsers    │      │ Device Detector │                       │
│  │ (parsers.py)│      │(device_detector)│                       │
│  │ • CDP       │      │ • YAML config   │                       │
│  │ • LLDP      │      │ • Pattern match │                       │
│  │ • Merge     │      │ • Capability    │                       │
│  └─────────────┘      └────────┬────────┘                       │
│                                │                                 │
│                                ▼                                 │
│                       ┌─────────────────┐                        │
│                       │  Configuration  │                        │
│                       │  (YAML file)    │                        │
│                       │ • Patterns      │                        │
│                       │ • Priorities    │                        │
│                       └─────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼ SSH Connections
┌─────────────────────────────────────────────────────────────────┐
│                      NETWORK DEVICES                            │
│                                                                  │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐             │
│   │ CORE-SW  │──────│ DIST-SW  │──────│ACCESS-SW │             │
│   │  (Seed)  │      │          │      │          │             │
│   └──────────┘      └──────────┘      └──────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Discovery Flow

```
1. USER SUBMITS FORM
   ├─ Seed IP: 192.168.1.1
   ├─ Device Type: cisco_ios
   ├─ Credentials: admin/password
   └─ Max Depth: 3

2. FLASK APP RECEIVES REQUEST
   └─ Validates inputs
   
3. TOPOLOGY DISCOVERER STARTS
   └─ Queue: [(192.168.1.1, cisco_ios, depth=0)]

4. FOR EACH DEVICE IN QUEUE:
   
   ┌─ CONNECT VIA SSH
   │  └─ Netmiko: ConnectHandler(host, device_type, creds)
   │
   ├─ GET HOSTNAME
   │  └─ Parse prompt: "CORE-SW-01#"
   │
   ├─ RUN DISCOVERY COMMANDS
   │  ├─ show cdp neighbors detail
   │  └─ show lldp neighbors detail
   │
   ├─ PARSE OUTPUTS
   │  ├─ CDP Parser extracts:
   │  │  • Remote hostname
   │  │  • Remote IP
   │  │  • Platform string
   │  │  • Capabilities
   │  │  • Local interface
   │  │  • Remote interface
   │  │
   │  ├─ LLDP Parser extracts:
   │  │  • System name
   │  │  • Management IP
   │  │  • System description
   │  │  • Capabilities
   │  │  • Port IDs
   │  │
   │  └─ Merge CDP + LLDP data
   │     └─ Deduplicate, combine best info
   │
   ├─ FOR EACH NEIGHBOR:
   │  │
   │  ├─ DETECT DEVICE TYPE
   │  │  ├─ Load YAML patterns
   │  │  ├─ Match platform string
   │  │  │  Example: "cisco WS-C3750" → cisco_ios
   │  │  ├─ Check capabilities
   │  │  │  • Has "Router" or "Switch"? → Continue
   │  │  │  • Otherwise → Skip (phone, AP, etc.)
   │  │  └─ Return: cisco_ios, cisco_xe, etc.
   │  │
   │  ├─ CREATE LINK OBJECT
   │  │  └─ Store: local_intf ↔ remote_intf + IP
   │  │
   │  └─ QUEUE FOR DISCOVERY
   │     └─ If: has_ip AND is_router/switch AND not_visited
   │        Add to queue: (neighbor_ip, detected_type, depth+1)
   │
   └─ DISCONNECT

5. REPEAT UNTIL:
   • Queue is empty, OR
   • Max depth reached

6. BUILD TOPOLOGY TREE
   ├─ Create adjacency graph
   ├─ Start from root device
   ├─ Recursively build tree structure
   └─ Format with:
      • Device names
      • Management IPs
      • Interface mappings
      • Protocol indicators

7. RENDER TO USER
   └─ Return HTML with:
      • Success message
      • Summary stats
      • Topology tree
```

## Data Structures

```python
# Device object
Device {
    hostname: "CORE-SW-01"
    mgmt_ip: "192.168.1.1"
    device_type: "cisco_ios"
    platform: "cisco WS-C4500X"
    links: [Link, Link, ...]
}

# Link object
Link {
    local_device: "CORE-SW-01"
    local_intf: "Gi1/0/1"
    remote_device: "DIST-SW-01"
    remote_intf: "Gi1/0/48"
    remote_ip: "192.168.1.10"
    protocols: ["CDP", "LLDP"]
}

# Topology graph
Topology {
    devices: {
        "CORE-SW-01": Device(...),
        "DIST-SW-01": Device(...),
        ...
    }
}
```

## File Interactions

```
app.py
  │
  ├─ Loads: templates/index.html
  │
  ├─ Imports: discovery.py
  │    │
  │    ├─ Imports: parsers.py
  │    │    └─ Functions: parse_cdp(), parse_lldp(), merge()
  │    │
  │    └─ Imports: device_detector.py
  │         │
  │         └─ Reads: config/device_type_patterns.yaml
  │
  └─ Writes: logs/app.log
```

## YAML Configuration Flow

```
config/device_type_patterns.yaml
              │
              ├─ Loaded by: DeviceTypeDetector
              │
              ├─ Parsed into: Python dict
              │
              └─ Used for:
                 │
                 ├─ Pattern matching
                 │   Platform string → Device type
                 │
                 ├─ Capability filtering
                 │   Router/Switch only
                 │
                 └─ Priority ranking
                     Higher priority = preferred match
```

## HTTP Request Flow

```
Browser                  Flask App                Network
   │                        │                        │
   │  POST /discover        │                        │
   ├───────────────────────>│                        │
   │                        │                        │
   │                        │  SSH connect           │
   │                        ├───────────────────────>│
   │                        │<───────────────────────┤
   │                        │  "CORE-SW-01#"         │
   │                        │                        │
   │                        │  show cdp neighbors    │
   │                        ├───────────────────────>│
   │                        │<───────────────────────┤
   │                        │  [CDP output]          │
   │                        │                        │
   │                        │  show lldp neighbors   │
   │                        ├───────────────────────>│
   │                        │<───────────────────────┤
   │                        │  [LLDP output]         │
   │                        │                        │
   │                        │  [Repeat for neighbors]│
   │                        │                        │
   │  HTML Response         │                        │
   │<───────────────────────┤                        │
   │  (Topology tree)       │                        │
```

## Component Responsibilities

| Component | Responsibility |
|-----------|---------------|
| app.py | Web interface, request handling |
| discovery.py | Network crawling, SSH management |
| parsers.py | Protocol output parsing |
| device_detector.py | Device type identification |
| device_type_patterns.yaml | Pattern configuration |
| index.html | User interface |

## Key Design Decisions

✅ **YAML for patterns** - Easy updates without code changes
✅ **Separate parsers** - Clean, testable modules
✅ **Device detector** - Centralized type detection logic
✅ **Queue-based discovery** - Breadth-first traversal
✅ **Capability filtering** - Only crawl relevant devices
✅ **Protocol merging** - Best data from CDP + LLDP
✅ **Loop prevention** - Track visited devices
✅ **Error isolation** - Failed device doesn't stop discovery
