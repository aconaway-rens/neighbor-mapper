# Network Neighbor Mapper

A Flask-based web application that discovers network topology using CDP and LLDP protocols. Automatically detects device types and recursively maps network neighbors.

## 🎯 Features

- **Web Interface** - Easy-to-use HTML form for discovery
- **Multi-Protocol** - Discovers neighbors via both CDP and LLDP
- **Smart Detection** - YAML-based device type detection
- **Recursive Discovery** - Automatically crawls neighbors (routers/switches only)
- **Interface Mapping** - Shows local and remote interface connections
- **Management IPs** - Displays IP addresses for discovered devices
- **Text-Based Map** - Clean ASCII tree visualization
- **Docker Ready** - Containerized for easy deployment

## 📋 Prerequisites

- Docker and Docker Compose
- Network access to devices
- SSH credentials with appropriate privileges
- Devices with CDP and/or LLDP enabled

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone or extract the project
cd neighbor-mapper-v2

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

Access the web interface at: **http://localhost:8000**

### Option 2: Docker Build

```bash
# Build the image
docker build -t neighbor-mapper .

# Run the container
docker run -d -p 8000:8000 --name neighbor-mapper neighbor-mapper

# View logs
docker logs -f neighbor-mapper
```

### Option 3: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
cd app
python app.py
```

## 🎮 Usage

1. **Open Web Interface** - Navigate to http://localhost:8000
2. **Enter Seed Device** - Provide IP address of starting device
3. **Select Device Type** - Choose the Netmiko device type from dropdown
4. **Enter Credentials** - SSH username and password
5. **Set Depth** - Choose how many hops to discover (1-5)
6. **Start Discovery** - Click "Start Discovery" button
7. **View Results** - See topology map with devices, interfaces, and IPs

## 📊 Example Output

```
CORE-SW-01 (192.168.1.1)
├─[CDP+LLDP] Gi1/0/1 ↔ Gi1/0/48 (192.168.1.10)
│   DIST-SW-01 (192.168.1.10)
│   └─[CDP+LLDP] Gi1/0/10 ↔ Gi0/1 (192.168.1.20)
│      ACCESS-SW-01 (192.168.1.20)
└─[CDP+LLDP] Gi1/0/2 ↔ Gi1/0/48 (192.168.1.11)
   DIST-SW-02 (192.168.1.11)
```

## ⚙️ Configuration

### Device Type Detection

Edit `config/device_type_patterns.yaml` to add or modify device type patterns:

```yaml
device_types:
  cisco_ios:
    platforms:
      - catalyst
      - c3750
      - c2960
    system_descriptions:
      - "Cisco IOS Software"
    priority: 50
```

**Pattern Matching:**
- `platforms`: Match against CDP platform string
- `system_descriptions`: Match against LLDP system description
- `priority`: Higher priority patterns are preferred (0-100)

**Add New Patterns:**
1. Edit `config/device_type_patterns.yaml`
2. Add platform or description patterns
3. Restart the container: `docker-compose restart`

### Discovery Settings

In `config/device_type_patterns.yaml`:

```yaml
discovery:
  max_depth: 3              # Default maximum hops
  connection_timeout: 15    # SSH connection timeout (seconds)
  command_timeout: 30       # Command execution timeout (seconds)
```

### Capability Filtering

Control which devices are crawled:

```yaml
allowed_capabilities:
  - Router    # Full word
  - Switch
  - R         # Abbreviated
  - S
  - B         # Bridge (switch)
```

Devices without these capabilities (like phones, access points) are ignored.

## 🗂️ Project Structure

```
neighbor-mapper-v2/
├── app/
│   ├── app.py              # Flask application
│   ├── discovery.py        # Topology discovery engine
│   ├── parsers.py          # CDP/LLDP parsers
│   └── device_detector.py  # Device type detection
├── config/
│   └── device_type_patterns.yaml  # Detection patterns
├── templates/
│   └── index.html          # Web interface
├── logs/                   # Application logs
├── Dockerfile              # Container definition
├── docker-compose.yml      # Docker Compose config
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔍 How It Works

1. **Initial Connection**
   - SSH to seed device using provided credentials
   - Extract hostname from prompt

2. **Neighbor Discovery**
   - Run `show cdp neighbors detail`
   - Run `show lldp neighbors detail`
   - Parse outputs to extract neighbor information

3. **Device Type Detection**
   - Match platform strings against YAML patterns
   - Determine appropriate Netmiko device type
   - Check capabilities (Router/Switch only)

4. **Recursive Crawl**
   - Queue neighbors for discovery
   - Repeat process for each neighbor
   - Track visited devices to avoid loops
   - Respect maximum depth setting

5. **Topology Rendering**
   - Build adjacency graph
   - Generate ASCII tree visualization
   - Show interface mappings and IPs

## 📝 Logs

Logs are written to `logs/app.log` and displayed in the container output.

**View logs:**
```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f neighbor-mapper

# Local file
tail -f logs/app.log
```

**Log Levels:**
- INFO: Discovery progress, device connections
- WARNING: Failed CDP/LLDP queries, skipped devices
- ERROR: Connection failures, authentication errors

## 🐛 Troubleshooting

### No neighbors found
- **Check:** CDP/LLDP enabled on devices
- **Command:** `show cdp neighbors` / `show lldp neighbors`
- **Fix:** `cdp run` / `lldp run` in global config

### Authentication failed
- **Check:** Username/password correct
- **Check:** Account has privilege level 15 or appropriate access
- **Fix:** Test SSH manually: `ssh user@device-ip`

### Connection timeout
- **Check:** Network connectivity to device
- **Check:** SSH enabled and accessible
- **Fix:** Verify firewall rules, ping device

### Wrong device type detected
- **Check:** Pattern matching in YAML config
- **Fix:** Add specific platform pattern for your device
- **Example:** Add `c9300-24p` to cisco_xe platforms

### Device skipped during crawl
- **Check:** Device capabilities
- **Reason:** Only Router/Switch devices are crawled
- **Fix:** Verify device is reporting R or S capability

## 🔒 Security Considerations

- **Credentials:** Passwords are not stored, only used during discovery
- **Network Access:** Ensure container can reach network devices
- **SSH Keys:** Currently uses password auth (key auth can be added)
- **HTTPS:** Consider adding TLS/SSL for production use
- **Authentication:** Add web app authentication for production

## 🚧 Limitations

- **SSH Only:** Telnet not supported
- **Cisco Focus:** Best tested on Cisco devices
- **Single Credential:** Uses same credentials for all devices
- **No Persistence:** Discovery results not saved (add database for this)
- **Text Output:** No graphical topology (can add vis.js, D3, etc.)

## 🔮 Future Enhancements

- [ ] Save topologies to database
- [ ] Export to formats (JSON, GraphML, CSV)
- [ ] Graphical topology visualization
- [ ] Multiple credential sets
- [ ] SSH key authentication
- [ ] Web authentication/authorization
- [ ] REST API endpoints
- [ ] Scheduled discoveries
- [ ] Change detection
- [ ] More vendor support

## 📄 License

Open source - feel free to modify and extend!

## 🤝 Contributing

To add support for new device types:

1. Edit `config/device_type_patterns.yaml`
2. Add platform/description patterns
3. Set appropriate priority
4. Test and submit PR

## 💡 Tips

- **Start small:** Use depth=1 for initial testing
- **Check logs:** Monitor logs during discovery
- **Update patterns:** Add patterns as you discover new device types
- **Test credentials:** Verify SSH access before running discovery
- **Network segments:** May need to run from jump host if devices are isolated
