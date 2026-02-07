# Quick Start Guide

## Get Running in 60 Seconds

### Step 1: Start the Application
```bash
docker-compose up -d
```

### Step 2: Open Browser
Navigate to: **http://localhost:8000**

### Step 3: Fill the Form
- **Seed IP:** `192.168.1.1` (your device IP)
- **Device Type:** Select from dropdown (e.g., Cisco IOS)
- **Username:** `admin` (your SSH username)
- **Password:** Your SSH password
- **Max Depth:** `3` (recommended)

### Step 4: Click "Start Discovery"
Wait 10-30 seconds for results

### Step 5: View Topology
See your network map with:
- Device hostnames
- Management IPs
- Interface connections
- Protocol used (CDP/LLDP)

## Example Output
```
CORE-SW (192.168.1.1)
├─[CDP+LLDP] Gi1/0/1 ↔ Gi0/48 (192.168.1.10)
│   DIST-SW-01 (192.168.1.10)
│   └─[CDP] Gi0/1 ↔ Gi0/1 (192.168.1.20)
│      ACCESS-SW-01 (192.168.1.20)
└─[LLDP] Gi1/0/2 ↔ Gi0/48 (192.168.1.11)
   DIST-SW-02 (192.168.1.11)
```

## Troubleshooting

**Can't connect to devices?**
- Verify SSH is enabled
- Check firewall rules
- Test: `ssh user@device-ip`

**No neighbors found?**
- Enable CDP: `cdp run`
- Enable LLDP: `lldp run`
- Verify: `show cdp neighbors`

**Wrong device type detected?**
- Edit `config/device_type_patterns.yaml`
- Add your platform string
- Restart: `docker-compose restart`

## Next Steps

1. **Add More Patterns** - Edit `config/device_type_patterns.yaml`
2. **Check Logs** - `docker-compose logs -f`
3. **Customize** - Modify templates, add features
4. **Deploy** - Use in production with HTTPS/auth

## Stop the Application
```bash
docker-compose down
```

## View Logs
```bash
docker-compose logs -f
```

## Update Configuration
```bash
# Edit the config
nano config/device_type_patterns.yaml

# Restart to apply changes
docker-compose restart
```

That's it! You're mapping networks! 🗺️
