# Changelog

All notable changes to Network Neighbor Mapper will be documented in this file.

## [1.0] - 2026-02-12 🎉

**First stable release!**

### Performance Improvements (CRITICAL)
- **20x faster discovery** - Reduced from 10+ minutes to 30 seconds for 9 devices
- Eliminated timeout retry loop - fail fast instead of trying all device types
- Aggressive timeout reductions:
  - Connection: 30s → 10s
  - Session: 60s → 20s
  - Auth: 30s → 10s
  - Commands: 30s → 15s
- Enabled fast_cli mode for faster command execution
- Reduced global_delay_factor from 2 to 1

### Bug Fixes (CRITICAL)
- Fixed device filtering - phones/APs/servers now properly respect checkbox settings
- Devices are only added to topology if their type filter is enabled
- Connection timeouts now properly raise errors instead of retrying all device types

### What's Included in 1.0
- Multi-vendor network discovery (CDP & LLDP)
- Interactive D3.js visualization with high-contrast colors
- Smart device categorization (routers, switches, firewalls, phones, APs, servers)
- L3 switch labeling
- Firewall detection by platform keywords
- Device type filtering
- Seed device highlighting with star marker
- PNG export with white background
- Abbreviated interface names
- Physics simulation controls
- Docker deployment
- Demo mode with mock multi-vendor network

## [0.3] - 2026-02-12

### Added
- L3 switch labeling - switches with routing capabilities now display "L3" label inside the node
- Firewall detection using platform/system description keywords
- Support for detecting phones, access points, and servers in mock network
- Added mock devices: IP phone (SEP001122334455), Access Point (AP-OFFICE-01), Server (SRV-DB-01)
- Debug logging for LLDP Management Address parsing

### Changed
- Device categorization now checks platform AND system description for firewall detection
- Improved device filtering - devices are added to topology even if not crawlable
- Split "crawlable" vs "displayable" logic - phones/APs/servers show in visualization but aren't crawled
- Firewall keywords include: Palo Alto, Fortinet, Checkpoint, Cisco ASA, Firepower, Sophos, SonicWall, WatchGuard, Barracuda, Juniper SRX, and PAN-OS

### Fixed
- Critical LLDP parser bug where IP addresses were being added to system_description instead of remote_ip field
- Categorization priority now correctly prioritizes switches over routers for dual-capability devices
- Seed device hostname resolution - now correctly shows star on seed device instead of using IP
- Tuple unpacking in should_crawl method after categorize_device return type change
- Mock network neighbors now properly include phones, APs, and servers

## [0.2] - 2026-02-11

### Added
- Interactive network visualization with D3.js force-directed graph
- High-contrast color scheme for better visibility
  - Router: Bright Red (#FF4444)
  - Switch: Cyan (#00D9FF)
  - Firewall: Bright Orange (#FFB800)
  - Access Point: Bright Green (#00FF88)
  - Server: Purple (#B84DFF)
  - Phone: Pink (#FF6B9D)
- Seed device marker (⭐ star) to show where discovery started
- Shortened interface names (G0/1 instead of GigabitEthernet0/1)
- Working physics simulation toggle with visual feedback
- Export to PNG functionality with white background
- Version numbering system
- Visualization documentation (VISUALIZATION.md)

### Changed
- PNG exports now use white background for better printing/sharing
- Physics toggle button shows current state (Freeze Layout/Resume Physics)
- Interface labels are abbreviated for cleaner display

### Fixed
- Link attribute naming mismatch (local_intf vs local_interface)
- PNG export contrast issues

## [0.1] - Initial Release

### Added
- Multi-protocol topology discovery (CDP and LLDP)
- Recursive neighbor discovery
- Multi-vendor support (Cisco, Arista, Juniper, Palo Alto, etc.)
- Intelligent device type detection
- Device type filtering
- ASCII tree visualization
- Docker support
- Demo mode with mock devices
- Web interface
