#!/usr/bin/env python3
"""
Debug script to test recursive discovery
Run this to see detailed logs of what's happening
"""

import sys
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

sys.path.insert(0, 'app')

from device_detector import DeviceTypeDetector
from discovery import TopologyDiscoverer, render_topology_tree

def test_recursive_discovery():
    """Test recursive discovery with demo devices"""
    print("\n" + "="*70)
    print("TESTING RECURSIVE DISCOVERY")
    print("="*70 + "\n")
    
    # Initialize
    detector = DeviceTypeDetector('config/device_type_patterns.yaml')
    
    # Filters: Routers and Switches only (default)
    filters = {
        'include_routers': True,
        'include_switches': True,
        'include_phones': False,
        'include_servers': False,
        'include_aps': False,
        'include_other': False,
    }
    
    discoverer = TopologyDiscoverer(detector, max_depth=3, filters=filters)
    
    print("Starting discovery from 192.168.1.1 (CORE-SW-01)")
    print("Max depth: 3")
    print("Filters: Routers + Switches only")
    print("-" * 70 + "\n")
    
    # Run discovery
    topology = discoverer.discover(
        seed_ip="192.168.1.1",
        seed_device_type="cisco_ios",
        username="demo",
        password="demo"
    )
    
    print("\n" + "="*70)
    print("DISCOVERY COMPLETE")
    print("="*70)
    print(f"Total devices discovered: {len(topology.devices)}")
    print(f"Devices visited: {len(discoverer.visited)}")
    print(f"\nVisited IPs: {sorted(discoverer.visited)}")
    
    print("\n" + "="*70)
    print("TOPOLOGY TREE")
    print("="*70)
    tree = render_topology_tree(topology)
    print(tree)
    
    print("\n" + "="*70)
    print("DEVICE DETAILS")
    print("="*70)
    for hostname, device in topology.devices.items():
        print(f"\n{hostname}:")
        print(f"  IP: {device.mgmt_ip}")
        print(f"  Type: {device.device_type}")
        print(f"  Links: {len(device.links)}")
        for link in device.links:
            print(f"    → {link.remote_device} ({link.protocols})")

if __name__ == "__main__":
    test_recursive_discovery()
