"""
Neighbor Mapper Flask Application
Web interface for network topology discovery
"""

import logging
from flask import Flask, render_template, request, jsonify, send_file
from device_detector import DeviceTypeDetector
from discovery import TopologyDiscoverer, render_topology_tree, DiscoveryError
from visualizer import NetworkVisualizer
import tempfile
import os

# Read version
VERSION = "0.2"
try:
    with open('/app/VERSION', 'r') as f:
        VERSION = f.read().strip()
except:
    pass

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
    ('paloalto_panos', 'Palo Alto PAN-OS'),
    ('mikrotik_routeros', 'MikroTik RouterOS'),
    ('fortinet', 'Fortinet FortiGate'),
    ('hp_procurve', 'HP ProCurve'),
    ('hp_comware', 'HPE Comware'),
    ('aruba_os', 'Aruba OS-CX'),
    ('dell_os10', 'Dell OS10'),
    ('dell_force10', 'Dell Force10'),
    ('extreme', 'Extreme ExtremeXOS'),
    ('extreme_vsp', 'Extreme VOSS'),
    ('ubiquiti_edge', 'Ubiquiti EdgeOS'),
    ('barracuda', 'Barracuda'),
]


@app.route('/')
def index():
    """Main page with discovery form"""
    return render_template('index.html', device_types=DEVICE_TYPES, version=VERSION)


@app.route('/discover', methods=['POST'])
def discover():
    """Handle discovery request"""
    # Get form data
    seed_ip = request.form.get('seed_ip', '').strip()
    device_type = request.form.get('device_type', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    max_depth = int(request.form.get('max_depth', 3))
    
    # Get filter settings
    filters = {
        'include_routers': request.form.get('include_routers') == 'true',
        'include_switches': request.form.get('include_switches') == 'true',
        'include_phones': request.form.get('include_phones') == 'true',
        'include_servers': request.form.get('include_servers') == 'true',
        'include_aps': request.form.get('include_aps') == 'true',
        'include_other': request.form.get('include_other') == 'true',
    }
    
    # Validate inputs
    if not all([seed_ip, device_type, username, password]):
        return render_template('index.html', 
                             device_types=DEVICE_TYPES,
                             version=VERSION,
                             error="All fields are required")
    
    logger.info(f"Discovery request: seed={seed_ip}, type={device_type}, user={username}, depth={max_depth}")
    logger.info(f"Filters: {filters}")
    
    try:
        # Create discoverer
        discoverer = TopologyDiscoverer(detector, max_depth=max_depth, filters=filters)
        
        # Run discovery
        topology = discoverer.discover(seed_ip, device_type, username, password)
        
        # Render topology as text tree
        tree_output = render_topology_tree(topology)
        
        # Prepare summary
        total_devices = len(topology.devices)
        
        # Count unique links (each edge only once, not both directions)
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
            'visited': list(discoverer.visited),
            'failed': discoverer.failed,
            'failed_count': len(discoverer.failed)
        }
        
        logger.info(f"Discovery complete: {total_devices} devices, {total_links} links")
        
        # Generate network visualization
        viz_file = None
        try:
            # Convert topology to dict format for visualizer
            topology_dict = {}
            for device_name, device in topology.devices.items():
                neighbors = []
                for link in device.links:
                    neighbors.append({
                        'neighbor_device': link.remote_device,
                        'local_interface': link.local_intf,
                        'remote_interface': link.remote_intf
                    })
                
                # Use device_category for visualization, fallback to 'unknown'
                device_category = device.device_category if device.device_category else 'unknown'
                
                topology_dict[device_name] = {
                    'device_type': device_category,  # Visualizer expects category here
                    'has_routing': device.has_routing,  # For L3 switch labeling
                    'neighbors': neighbors
                }
            
            # Generate visualization with seed device
            # Find the hostname that corresponds to the seed IP
            seed_hostname = None
            for device_name, device in topology.devices.items():
                if device.mgmt_ip == seed_ip:
                    seed_hostname = device_name
                    break
            
            visualizer = NetworkVisualizer(topology_dict, seed_device=seed_hostname)
            viz_filename = f"topology_{seed_ip.replace('.', '_')}.html"
            viz_path = os.path.join('/tmp', viz_filename)
            visualizer.generate_html(viz_path)
            viz_file = viz_filename
            logger.info(f"Generated visualization: {viz_path} (seed: {seed_hostname})")
        except Exception as e:
            logger.warning(f"Failed to generate visualization: {e}")
        
        return render_template('index.html',
                             device_types=DEVICE_TYPES,
                             version=VERSION,
                             topology=tree_output,
                             summary=summary,
                             visualization=viz_file,
                             success=True)
    
    except DiscoveryError as e:
        logger.error(f"Discovery error: {e.message}")
        return render_template('index.html',
                             device_types=DEVICE_TYPES,
                             version=VERSION,
                             error=f"Discovery failed: {e.message}")
    
    except Exception as e:
        logger.exception("Unexpected error during discovery")
        return render_template('index.html',
                             device_types=DEVICE_TYPES,
                             version=VERSION,
                             error=f"Unexpected error: {str(e)}")


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


@app.route('/visualization/<filename>')
def serve_visualization(filename):
    """Serve generated visualization files"""
    try:
        file_path = os.path.join('/tmp', filename)
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='text/html')
        else:
            return "Visualization file not found", 404
    except Exception as e:
        logger.error(f"Error serving visualization: {e}")
        return "Error loading visualization", 500


if __name__ == '__main__':
    logger.info("Starting Neighbor Mapper application")
    app.run(host='0.0.0.0', port=8000, debug=False)
