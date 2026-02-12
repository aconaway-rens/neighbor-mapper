#!/usr/bin/env python3
"""
Test script to generate a network visualization from mock topology
"""

import sys
sys.path.insert(0, '/mnt/user-data/outputs/neighbor-mapper-main/app')

from visualizer import NetworkVisualizer


def create_demo_topology():
    """Create a demo topology based on the mock device structure"""
    # This represents the mock network topology
    topology = {
        'core-router-01.acme.local': {
            'device_type': 'router',
            'neighbors': [
                {
                    'neighbor_device': 'dist-switch-01.acme.local',
                    'local_interface': 'GigabitEthernet0/0/0',
                    'remote_interface': 'TenGigabitEthernet1/0/1'
                },
                {
                    'neighbor_device': 'dist-switch-02.acme.local',
                    'local_interface': 'GigabitEthernet0/0/1',
                    'remote_interface': 'TenGigabitEthernet1/0/1'
                },
                {
                    'neighbor_device': 'border-fw-01.acme.local',
                    'local_interface': 'GigabitEthernet0/0/2',
                    'remote_interface': 'ethernet1/1'
                }
            ]
        },
        'dist-switch-01.acme.local': {
            'device_type': 'switch',
            'neighbors': [
                {
                    'neighbor_device': 'core-router-01.acme.local',
                    'local_interface': 'TenGigabitEthernet1/0/1',
                    'remote_interface': 'GigabitEthernet0/0/0'
                },
                {
                    'neighbor_device': 'access-switch-01.acme.local',
                    'local_interface': 'GigabitEthernet1/0/1',
                    'remote_interface': 'GigabitEthernet0/1'
                },
                {
                    'neighbor_device': 'access-switch-02.acme.local',
                    'local_interface': 'GigabitEthernet1/0/2',
                    'remote_interface': 'GigabitEthernet0/1'
                },
                {
                    'neighbor_device': 'wireless-ap-01.acme.local',
                    'local_interface': 'GigabitEthernet1/0/10',
                    'remote_interface': 'GigabitEthernet0'
                }
            ]
        },
        'dist-switch-02.acme.local': {
            'device_type': 'switch',
            'neighbors': [
                {
                    'neighbor_device': 'core-router-01.acme.local',
                    'local_interface': 'TenGigabitEthernet1/0/1',
                    'remote_interface': 'GigabitEthernet0/0/1'
                },
                {
                    'neighbor_device': 'access-switch-01.acme.local',
                    'local_interface': 'GigabitEthernet1/0/1',
                    'remote_interface': 'GigabitEthernet0/2'
                },
                {
                    'neighbor_device': 'access-switch-03.acme.local',
                    'local_interface': 'GigabitEthernet1/0/3',
                    'remote_interface': 'GigabitEthernet0/1'
                }
            ]
        },
        'access-switch-01.acme.local': {
            'device_type': 'switch',
            'neighbors': [
                {
                    'neighbor_device': 'dist-switch-01.acme.local',
                    'local_interface': 'GigabitEthernet0/1',
                    'remote_interface': 'GigabitEthernet1/0/1'
                },
                {
                    'neighbor_device': 'dist-switch-02.acme.local',
                    'local_interface': 'GigabitEthernet0/2',
                    'remote_interface': 'GigabitEthernet1/0/1'
                },
                {
                    'neighbor_device': 'server-01.acme.local',
                    'local_interface': 'GigabitEthernet0/10',
                    'remote_interface': 'eth0'
                },
                {
                    'neighbor_device': 'phone-101',
                    'local_interface': 'FastEthernet0/15',
                    'remote_interface': 'eth0'
                }
            ]
        },
        'access-switch-02.acme.local': {
            'device_type': 'switch',
            'neighbors': [
                {
                    'neighbor_device': 'dist-switch-01.acme.local',
                    'local_interface': 'GigabitEthernet0/1',
                    'remote_interface': 'GigabitEthernet1/0/2'
                },
                {
                    'neighbor_device': 'phone-102',
                    'local_interface': 'FastEthernet0/12',
                    'remote_interface': 'eth0'
                },
                {
                    'neighbor_device': 'phone-103',
                    'local_interface': 'FastEthernet0/13',
                    'remote_interface': 'eth0'
                }
            ]
        },
        'access-switch-03.acme.local': {
            'device_type': 'switch',
            'neighbors': [
                {
                    'neighbor_device': 'dist-switch-02.acme.local',
                    'local_interface': 'GigabitEthernet0/1',
                    'remote_interface': 'GigabitEthernet1/0/3'
                },
                {
                    'neighbor_device': 'server-02.acme.local',
                    'local_interface': 'GigabitEthernet0/20',
                    'remote_interface': 'eth0'
                }
            ]
        },
        'border-fw-01.acme.local': {
            'device_type': 'firewall',
            'neighbors': [
                {
                    'neighbor_device': 'core-router-01.acme.local',
                    'local_interface': 'ethernet1/1',
                    'remote_interface': 'GigabitEthernet0/0/2'
                }
            ]
        },
        'wireless-ap-01.acme.local': {
            'device_type': 'access_point',
            'neighbors': [
                {
                    'neighbor_device': 'dist-switch-01.acme.local',
                    'local_interface': 'GigabitEthernet0',
                    'remote_interface': 'GigabitEthernet1/0/10'
                }
            ]
        },
        'server-01.acme.local': {
            'device_type': 'server',
            'neighbors': [
                {
                    'neighbor_device': 'access-switch-01.acme.local',
                    'local_interface': 'eth0',
                    'remote_interface': 'GigabitEthernet0/10'
                }
            ]
        },
        'server-02.acme.local': {
            'device_type': 'server',
            'neighbors': [
                {
                    'neighbor_device': 'access-switch-03.acme.local',
                    'local_interface': 'eth0',
                    'remote_interface': 'GigabitEthernet0/20'
                }
            ]
        },
        'phone-101': {
            'device_type': 'phone',
            'neighbors': [
                {
                    'neighbor_device': 'access-switch-01.acme.local',
                    'local_interface': 'eth0',
                    'remote_interface': 'FastEthernet0/15'
                }
            ]
        },
        'phone-102': {
            'device_type': 'phone',
            'neighbors': [
                {
                    'neighbor_device': 'access-switch-02.acme.local',
                    'local_interface': 'eth0',
                    'remote_interface': 'FastEthernet0/12'
                }
            ]
        },
        'phone-103': {
            'device_type': 'phone',
            'neighbors': [
                {
                    'neighbor_device': 'access-switch-02.acme.local',
                    'local_interface': 'eth0',
                    'remote_interface': 'FastEthernet0/13'
                }
            ]
        }
    }
    
    return topology


def main():
    print("Generating network topology visualization from demo data...")
    
    # Generate demo topology
    topology_dict = create_demo_topology()
    
    # Set seed device
    seed_device = 'core-router-01.acme.local'
    
    print(f"\nTopology contains {len(topology_dict)} devices:")
    print(f"Seed device: {seed_device} ⭐")
    print("")
    device_counts = {}
    for device_name, info in topology_dict.items():
        device_type = info['device_type']
        device_counts[device_type] = device_counts.get(device_type, 0) + 1
        seed_marker = " ⭐" if device_name == seed_device else ""
        print(f"  - {device_name} ({info['device_type']}) with {len(info['neighbors'])} neighbors{seed_marker}")
    
    print(f"\nDevice type breakdown:")
    for dtype, count in sorted(device_counts.items()):
        print(f"  • {dtype}: {count}")
    
    # Generate interactive HTML visualization
    print("\n" + "="*60)
    print("Generating Interactive HTML Visualization")
    print("="*60)
    visualizer = NetworkVisualizer(topology_dict, seed_device=seed_device)
    html_file = visualizer.generate_html('/mnt/user-data/outputs/network_topology_demo.html')
    print(f"✓ Interactive HTML saved to: {html_file}")
    
    # Generate static SVG visualization
    print("\n" + "="*60)
    print("Generating Static SVG Visualization")
    print("="*60)
    svg_file = visualizer.generate_static_svg('/mnt/user-data/outputs/network_topology_demo.svg')
    print(f"✓ Static SVG saved to: {svg_file}")
    
    print("\n" + "="*60)
    print("SUCCESS! Network visualizations have been generated.")
    print("="*60)
    print("\nThe interactive HTML includes:")
    print("  ✓ High-contrast color-coded nodes by device type")
    print("  ✓ Short hostname labels")
    print("  ✓ Shortened interface labels (G0/1 instead of GigabitEthernet0/1)")
    print("  ✓ Seed device marked with ⭐ star")
    print("  ✓ Drag-and-drop repositioning")
    print("  ✓ Zoom and pan controls")
    print("  ✓ Freeze/Resume physics simulation")
    print("  ✓ Export to PNG button")
    print("  ✓ Interactive tooltips")
    print("  ✓ Legend showing device types")
    print("  ✓ Dark theme optimized for readability")
    print("\nOpen the HTML file in a web browser to explore!")
    print("\nHigh-Contrast Color scheme:")
    print("  • Router: Bright Red (#FF4444)")
    print("  • Switch: Cyan (#00D9FF)")
    print("  • Firewall: Bright Orange (#FFB800)")
    print("  • Access Point: Bright Green (#00FF88)")
    print("  • Server: Purple (#B84DFF)")
    print("  • Phone: Pink (#FF6B9D)")


if __name__ == '__main__':
    main()

