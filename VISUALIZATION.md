# Network Visualization Feature

## Overview

The Neighbor Mapper now includes powerful network visualization capabilities that generate interactive network diagrams from discovered topology data.

## Features

### Interactive HTML Visualization

The primary visualization output is an interactive HTML page that includes:

- **High-Contrast Color-Coded Nodes**: Each device type has a vibrant, distinct color for better visibility
  - Router: Bright Red (#FF4444)
  - Switch: Cyan (#00D9FF)
  - Firewall: Bright Orange (#FFB800)
  - Access Point: Bright Green (#00FF88)
  - Server: Purple (#B84DFF)
  - Phone: Pink (#FF6B9D)
  - Unknown: Gray (#999999)

- **Short Hostname Labels**: Displays only the hostname (before the first dot) for cleaner visualization

- **Shortened Interface Labels**: Automatically abbreviates interface names for readability
  - `GigabitEthernet0/0/1` → `G0/0/1`
  - `TenGigabitEthernet1/0/1` → `Te1/0/1`
  - `FastEthernet0/1` → `F0/1`
  - Shows interface names at both ends of each connection
  - Source interface labeled at 1/4 point along the link
  - Destination interface labeled at 3/4 point along the link

- **Seed Device Marker**: The device where discovery started is marked with a ⭐ star in the center of its node

- **Interactive Controls**:
  - **Drag & Drop**: Click and drag nodes to reposition them
  - **Zoom & Pan**: Scroll to zoom, drag background to pan
  - **Freeze/Resume Physics**: Toggle button that:
    - Shows "Freeze Layout" (teal) when physics is active
    - Shows "Resume Physics" (red) when frozen
    - Actually stops/starts the force simulation
  - **Reset View**: Button to return to default zoom/position
  - **Export to PNG**: Download the current view as a high-resolution PNG image

- **Tooltips**: Hover over nodes to see full device information including seed device indicator

- **Legend**: Color-coded legend showing all device types and seed device marker

- **Dark Theme**: Optimized for readability with a dark background

### Static SVG Visualization

An alternative static SVG output is also available for:
- Printing
- Documentation
- Situations where JavaScript is not available

## Usage

### From Web Interface

1. Run a discovery as normal
2. After successful discovery, click the "🌐 View Interactive Network Diagram" button
3. The visualization opens in a new tab

### Programmatic Usage

```python
from visualizer import NetworkVisualizer

# Prepare topology data in dictionary format
topology_dict = {
    'device1.example.com': {
        'device_type': 'router',
        'neighbors': [
            {
                'neighbor_device': 'device2.example.com',
                'local_interface': 'GigabitEthernet0/0',
                'remote_interface': 'GigabitEthernet0/1'
            }
        ]
    },
    # ... more devices
}

# Create visualizer with optional seed device
visualizer = NetworkVisualizer(topology_dict, seed_device='device1.example.com')

# Generate interactive HTML
visualizer.generate_html('output.html')

# Or generate static SVG
visualizer.generate_static_svg('output.svg')
```

Note: Interface names are automatically shortened in the visualization (e.g., `GigabitEthernet0/0` becomes `G0/0`).

### Test/Demo Mode

Generate a visualization from the demo topology:

```bash
cd neighbor-mapper-main
python3 test_visualization.py
```

This creates:
- `network_topology_demo.html` - Interactive visualization
- `network_topology_demo.svg` - Static SVG diagram

## Technical Details

### Graph Layout Algorithm

The interactive visualization uses D3.js force-directed graph layout with:
- **Link Force**: Maintains consistent edge lengths (150px default)
- **Charge Force**: Nodes repel each other (-300 strength)
- **Center Force**: Pulls graph toward center
- **Collision Force**: Prevents node overlap (40px radius)

### Data Format

The visualizer expects topology data in this format:

```python
{
    'device_hostname': {
        'device_type': 'router|switch|firewall|access_point|server|phone|unknown',
        'neighbors': [
            {
                'neighbor_device': 'neighbor_hostname',
                'local_interface': 'interface_name',
                'remote_interface': 'interface_name'
            }
        ]
    }
}
```

### Dependencies

The interactive HTML visualization uses:
- **D3.js v7** (loaded via CDN)
- No other external dependencies required
- Pure JavaScript/CSS, no build process needed

### Browser Compatibility

The visualization works in all modern browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Examples

### Small Network (5-10 devices)
Perfect size for default settings. All nodes visible, easy to navigate.

### Medium Network (10-30 devices)
May need to zoom out initially. Physics simulation helps organize layout.

### Large Network (30+ devices)
- Consider filtering by device type
- Use zoom controls extensively
- Freeze physics once satisfied with layout
- May benefit from multiple visualizations (one per section)

## Tips for Best Results

1. **Let Physics Settle**: Wait a few seconds after loading for the graph to stabilize
2. **Manual Adjustment**: Drag key nodes to better positions after physics settles
3. **Freeze When Happy**: Click "Freeze Layout" to lock the layout in place - button turns red
4. **Resume If Needed**: Click "Resume Physics" (red button) to restart the simulation
5. **Export Your Work**: Use "Export to PNG" to save high-resolution images of your network
6. **Save Screenshots**: Browser screenshot tools work great with frozen layout
7. **Filter First**: Use device type filters during discovery to reduce clutter
8. **Find Seed Device**: Look for the ⭐ star to identify where discovery started

## Troubleshooting

### Nodes Overlap
- Drag nodes apart manually
- Increase collision radius in code (default: 40px)
- Filter out less important device types

### Graph Too Spread Out
- Decrease link distance in code (default: 150px)
- Zoom in using scroll wheel

### Can't Read Interface Labels
- Zoom in on specific connections
- Interface labels are positioned at 1/4 and 3/4 points along links

### Performance Issues (Large Networks)
- Filter devices during discovery
- Generate multiple smaller visualizations
- Use static SVG instead of interactive HTML

## Future Enhancements

Potential future features:
- Export to PNG/PDF
- Hierarchical layout options
- Group nodes by subnet or location
- Link bandwidth/status indicators
- Time-based topology comparison
- Integration with network monitoring data
