"""
Neighbor Mapper Flask Application
Web interface for network topology discovery
"""

import logging
from flask import Flask, render_template, request, jsonify
from device_detector import DeviceTypeDetector
from discovery import TopologyDiscoverer, render_topology_tree, DiscoveryError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize device type detector
detector = DeviceTypeDetector()

# Common device types for dropdown
DEVICE_TYPES = [
    ('cisco_ios', 'Cisco IOS'),
    ('cisco_xe', 'Cisco IOS-XE'),
    ('cisco_nxos', 'Cisco NX-OS'),
    ('cisco_xr', 'Cisco IOS-XR'),
    ('arista_eos', 'Arista EOS'),
    ('juniper_junos', 'Juniper JunOS'),
]


@app.route('/')
def index():
    """Main page with discovery form"""
    return render_template('index.html', device_types=DEVICE_TYPES)


@app.route('/discover', methods=['POST'])
def discover():
    """Handle discovery request"""
    # Get form data
    seed_ip = request.form.get('seed_ip', '').strip()
    device_type = request.form.get('device_type', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    max_depth = int(request.form.get('max_depth', 3))
    
    # Validate inputs
    if not all([seed_ip, device_type, username, password]):
        return render_template('index.html', 
                             device_types=DEVICE_TYPES,
                             error="All fields are required")
    
    logger.info(f"Discovery request: seed={seed_ip}, type={device_type}, user={username}, depth={max_depth}")
    
    try:
        # Create discoverer
        discoverer = TopologyDiscoverer(detector, max_depth=max_depth)
        
        # Run discovery
        topology = discoverer.discover(seed_ip, device_type, username, password)
        
        # Render topology as text tree
        tree_output = render_topology_tree(topology)
        
        # Prepare summary
        total_devices = len(topology.devices)
        unique_links = set()
        for device in topology.devices.values():
            for link in device.links:
                # Create a sorted tuple so (A,B) and (B,A) are the same
                link_pair = tuple(sorted([link.local_device, link.remote_device]))
                unique_links.add(link_pair)
        total_links = len(unique_links)
        
        summary = {
            'devices': total_devices,
            'links': total_links,
            'visited': list(discoverer.visited)
        }
        
        logger.info(f"Discovery complete: {total_devices} devices, {total_links} links")
        
        return render_template('index.html',
                             device_types=DEVICE_TYPES,
                             topology=tree_output,
                             summary=summary,
                             success=True)
    
    except DiscoveryError as e:
        logger.error(f"Discovery error: {e.message}")
        return render_template('index.html',
                             device_types=DEVICE_TYPES,
                             error=f"Discovery failed: {e.message}")
    
    except Exception as e:
        logger.exception("Unexpected error during discovery")
        return render_template('index.html',
                             device_types=DEVICE_TYPES,
                             error=f"Unexpected error: {str(e)}")


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    logger.info("Starting Neighbor Mapper application")
    app.run(host='0.0.0.0', port=8000, debug=False)
