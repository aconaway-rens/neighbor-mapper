"""
Network Topology Visualizer
Generates interactive HTML network diagrams using D3.js force-directed graph
"""

import json
import re
from typing import Dict, List, Set, Tuple


class NetworkVisualizer:
    """Generates interactive network topology visualizations"""
    
    # Device type color scheme - Higher contrast colors
    DEVICE_COLORS = {
        'router': '#FF4444',      # Bright Red
        'switch': '#00D9FF',      # Cyan
        'firewall': '#FFB800',    # Bright Orange
        'access_point': '#00FF88', # Bright Green
        'server': '#B84DFF',      # Purple
        'phone': '#FF6B9D',       # Pink
        'unknown': '#999999'      # Gray
    }
    
    @staticmethod
    def shorten_interface_name(interface: str) -> str:
        """
        Shorten interface names for cleaner display
        Examples:
            GigabitEthernet0/0/1 -> G0/0/1
            TenGigabitEthernet1/0/1 -> Te1/0/1
            FastEthernet0/1 -> F0/1
            ethernet1/1 -> e1/1
        """
        # Common interface name abbreviations
        replacements = [
            (r'GigabitEthernet', 'G'),
            (r'TenGigabitEthernet', 'Te'),
            (r'FastEthernet', 'F'),
            (r'Ethernet', 'E'),
            (r'ethernet', 'e'),
            (r'Port-channel', 'Po'),
            (r'Vlan', 'Vl'),
        ]
        
        result = interface
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result
    
    def __init__(self, topology_data: Dict, seed_device: str = None):
        """
        Initialize visualizer with topology data
        
        Args:
            topology_data: Dictionary containing devices and connections
            seed_device: Optional seed device name to highlight
        """
        self.topology = topology_data
        self.seed_device = seed_device
        self.nodes = []
        self.edges = []
        
    def generate_graph_data(self):
        """Convert topology data to nodes and edges for visualization"""
        # Track unique devices
        device_set: Set[str] = set()
        
        # Collect all unique devices from connections
        for device_name, device_info in self.topology.items():
            device_set.add(device_name)
            for neighbor in device_info.get('neighbors', []):
                device_set.add(neighbor['neighbor_device'])
        
        # Create nodes
        for device_name in device_set:
            device_info = self.topology.get(device_name, {})
            device_type = device_info.get('device_type', 'unknown')
            has_routing = device_info.get('has_routing', False)
            
            # Extract short hostname (everything before first dot)
            short_name = device_name.split('.')[0]
            
            # Check if this is the seed device
            is_seed = (device_name == self.seed_device)
            
            node = {
                'id': device_name,
                'label': short_name,
                'type': device_type,
                'color': self.DEVICE_COLORS.get(device_type, self.DEVICE_COLORS['unknown']),
                'full_name': device_name,
                'is_seed': is_seed,
                'has_routing': has_routing
            }
            self.nodes.append(node)
        
        # Create edges with interface labels
        edge_set = set()  # Track edges to avoid duplicates
        
        for device_name, device_info in self.topology.items():
            for neighbor in device_info.get('neighbors', []):
                neighbor_device = neighbor['neighbor_device']
                local_int = neighbor['local_interface']
                remote_int = neighbor['remote_interface']
                
                # Shorten interface names
                local_int_short = self.shorten_interface_name(local_int)
                remote_int_short = self.shorten_interface_name(remote_int)
                
                # Create a unique edge identifier (sorted to avoid duplicates)
                edge_id = tuple(sorted([device_name, neighbor_device]))
                
                if edge_id not in edge_set:
                    edge = {
                        'source': device_name,
                        'target': neighbor_device,
                        'local_interface': local_int_short,
                        'remote_interface': remote_int_short
                    }
                    self.edges.append(edge)
                    edge_set.add(edge_id)
    
    def generate_html(self, output_file: str = 'network_topology.html'):
        """
        Generate interactive HTML visualization
        
        Args:
            output_file: Path to output HTML file
        """
        self.generate_graph_data()
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Network Topology Map</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1a1a1a;
            color: #ffffff;
        }}
        
        #header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        h1 {{
            margin: 0;
            color: #4ECDC4;
        }}
        
        #legend {{
            position: absolute;
            top: 80px;
            right: 20px;
            background: rgba(42, 42, 42, 0.9);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #4ECDC4;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }}
        
        #graph {{
            border: 1px solid #333;
            background-color: #0d1117;
            border-radius: 8px;
        }}
        
        .link {{
            stroke: #999;
            stroke-opacity: 0.6;
            stroke-width: 2px;
        }}
        
        .link:hover {{
            stroke: #4ECDC4;
            stroke-opacity: 1;
            stroke-width: 3px;
        }}
        
        .node {{
            cursor: pointer;
            stroke: #fff;
            stroke-width: 2px;
        }}
        
        .node:hover {{
            stroke: #4ECDC4;
            stroke-width: 3px;
        }}
        
        .node-label {{
            fill: #ffffff;
            font-size: 12px;
            font-weight: bold;
            text-anchor: middle;
            pointer-events: none;
            text-shadow: 0 0 3px #000, 0 0 3px #000, 0 0 3px #000;
        }}
        
        .interface-label {{
            fill: #FFE66D;
            font-size: 10px;
            pointer-events: none;
            text-shadow: 0 0 2px #000, 0 0 2px #000;
        }}
        
        .tooltip {{
            position: absolute;
            background: rgba(42, 42, 42, 0.95);
            border: 1px solid #4ECDC4;
            border-radius: 5px;
            padding: 10px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 12px;
        }}
        
        #controls {{
            position: absolute;
            top: 80px;
            left: 20px;
            background: rgba(42, 42, 42, 0.9);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #4ECDC4;
        }}
        
        button {{
            background: #4ECDC4;
            color: #000;
            border: none;
            padding: 8px 15px;
            margin: 5px 0;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            width: 100%;
        }}
        
        button:hover {{
            background: #3db8b0;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>🌐 Network Topology Map</h1>
        <p>Interactive visualization - Drag nodes to reposition | Scroll to zoom | Click nodes for details</p>
    </div>
    
    <div id="controls">
        <h3 style="margin-top: 0;">Controls</h3>
        <button onclick="resetZoom()">Reset View</button>
        <button id="physicsBtn" onclick="togglePhysics()">Freeze Layout</button>
        <button onclick="exportToPNG()">Export to PNG</button>
    </div>
    
    <div id="legend">
        <h3 style="margin-top: 0;">Device Types</h3>
        <div class="legend-item">
            <div class="legend-color" style="background-color: {self.DEVICE_COLORS['router']}"></div>
            <span>Router</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: {self.DEVICE_COLORS['switch']}"></div>
            <span>Switch</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: {self.DEVICE_COLORS['firewall']}"></div>
            <span>Firewall</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: {self.DEVICE_COLORS['access_point']}"></div>
            <span>Access Point</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: {self.DEVICE_COLORS['server']}"></div>
            <span>Server</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: {self.DEVICE_COLORS['phone']}"></div>
            <span>IP Phone</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: {self.DEVICE_COLORS['unknown']}"></div>
            <span>Unknown</span>
        </div>
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #555;">
            <div class="legend-item">
                <span style="font-size: 20px; margin-right: 10px;">⭐</span>
                <span>Seed Device</span>
            </div>
        </div>
    </div>
    
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        // Graph data
        const nodes = {json.dumps(self.nodes, indent=8)};
        
        const links = {json.dumps(self.edges, indent=8)};
        
        // Set up the SVG
        const width = window.innerWidth - 40;
        const height = window.innerHeight - 180;
        
        const svg = d3.select("body")
            .append("svg")
            .attr("id", "graph")
            .attr("width", width)
            .attr("height", height);
        
        const g = svg.append("g");
        
        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});
        
        svg.call(zoom);
        
        // Create the simulation
        let simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(40));
        
        // Create links
        const link = g.append("g")
            .selectAll("line")
            .data(links)
            .enter()
            .append("line")
            .attr("class", "link");
        
        // Create interface labels for links
        const linkLabels = g.append("g")
            .selectAll("g")
            .data(links)
            .enter()
            .append("g");
        
        // Source interface label
        linkLabels.append("text")
            .attr("class", "interface-label")
            .attr("dy", -5)
            .text(d => d.local_interface);
        
        // Target interface label
        linkLabels.append("text")
            .attr("class", "interface-label")
            .attr("dy", -5)
            .text(d => d.remote_interface);
        
        // Create nodes
        const node = g.append("g")
            .selectAll("circle")
            .data(nodes)
            .enter()
            .append("circle")
            .attr("class", "node")
            .attr("r", 25)
            .attr("fill", d => d.color)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended))
            .on("mouseover", showTooltip)
            .on("mouseout", hideTooltip)
            .on("click", nodeClicked);
        
        // Create node labels
        const nodeLabels = g.append("g")
            .selectAll("text")
            .data(nodes)
            .enter()
            .append("text")
            .attr("class", "node-label")
            .attr("dy", 40)
            .text(d => d.label);
        
        // Create seed device markers (stars)
        const seedMarkers = g.append("g")
            .selectAll("text")
            .data(nodes.filter(d => d.is_seed))
            .enter()
            .append("text")
            .attr("class", "seed-marker")
            .attr("text-anchor", "middle")
            .attr("dy", 5)
            .style("font-size", "20px")
            .style("pointer-events", "none")
            .text("⭐");
        
        // Create L3 labels for switches with routing capability
        const l3Labels = g.append("g")
            .selectAll("text")
            .data(nodes.filter(d => d.type === 'switch' && d.has_routing))
            .enter()
            .append("text")
            .attr("class", "l3-label")
            .attr("text-anchor", "middle")
            .attr("dy", 5)
            .style("font-size", "12px")
            .style("font-weight", "bold")
            .style("fill", "#FFFFFF")
            .style("pointer-events", "none")
            .text("L3");
        
        // Tooltip
        const tooltip = d3.select("#tooltip");
        
        // Update positions on each tick
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
            
            nodeLabels
                .attr("x", d => d.x)
                .attr("y", d => d.y);
            
            seedMarkers
                .attr("x", d => d.x)
                .attr("y", d => d.y);
            
            l3Labels
                .attr("x", d => d.x)
                .attr("y", d => d.y);
            
            // Position interface labels along links
            linkLabels.each(function(d) {{
                const labels = d3.select(this).selectAll("text");
                const dx = d.target.x - d.source.x;
                const dy = d.target.y - d.source.y;
                const len = Math.sqrt(dx * dx + dy * dy);
                
                // Source label (1/4 along the link)
                labels.nodes()[0] && d3.select(labels.nodes()[0])
                    .attr("x", d.source.x + dx * 0.25)
                    .attr("y", d.source.y + dy * 0.25);
                
                // Target label (3/4 along the link)
                labels.nodes()[1] && d3.select(labels.nodes()[1])
                    .attr("x", d.source.x + dx * 0.75)
                    .attr("y", d.source.y + dy * 0.75);
            }});
        }});
        
        // Drag functions
        function dragstarted(event) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }}
        
        function dragged(event) {{
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }}
        
        function dragended(event) {{
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }}
        
        // Tooltip functions
        function showTooltip(event, d) {{
            const seedText = d.is_seed ? '<br><strong style="color: #FFD700;">⭐ SEED DEVICE</strong>' : '';
            tooltip
                .style("opacity", 1)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px")
                .html(`
                    <strong>${{d.full_name}}</strong><br>
                    Type: ${{d.type}}<br>
                    Short name: ${{d.label}}${{seedText}}
                `);
        }}
        
        function hideTooltip() {{
            tooltip.style("opacity", 0);
        }}
        
        function nodeClicked(event, d) {{
            console.log("Clicked node:", d);
            const seedInfo = d.is_seed ? '\\n⭐ SEED DEVICE' : '';
            alert(`Device: ${{d.full_name}}\\nType: ${{d.type}}${{seedInfo}}`);
        }}
        
        // Control functions
        function resetZoom() {{
            svg.transition().duration(750).call(
                zoom.transform,
                d3.zoomIdentity
            );
        }}
        
        let physicsEnabled = true;
        const physicsBtn = document.getElementById('physicsBtn');
        
        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            if (physicsEnabled) {{
                physicsBtn.textContent = 'Freeze Layout';
                physicsBtn.style.background = '#4ECDC4';
                simulation.alphaTarget(0.3).restart();
                setTimeout(() => simulation.alphaTarget(0), 1000);
            }} else {{
                physicsBtn.textContent = 'Resume Physics';
                physicsBtn.style.background = '#FF6B6B';
                simulation.stop();
            }}
        }}
        
        function exportToPNG() {{
            // Get the SVG element and its dimensions
            const svgElement = document.getElementById('graph');
            const bbox = g.node().getBBox();
            const padding = 50;
            
            // Create a canvas
            const canvas = document.createElement('canvas');
            const scale = 3; // Higher resolution for better quality
            canvas.width = (bbox.width + padding * 2) * scale;
            canvas.height = (bbox.height + padding * 2) * scale;
            const ctx = canvas.getContext('2d');
            
            // Scale for higher resolution
            ctx.scale(scale, scale);
            
            // Fill with WHITE background for better visibility
            ctx.fillStyle = '#FFFFFF';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Clone the SVG and modify colors for light background
            const svgClone = svgElement.cloneNode(true);
            
            // Change text colors to black for visibility on white
            svgClone.querySelectorAll('.node-label').forEach(label => {{
                label.setAttribute('fill', '#000000');
                label.style.textShadow = 'none';
            }});
            
            svgClone.querySelectorAll('.interface-label').forEach(label => {{
                label.setAttribute('fill', '#CC6600');
                label.style.textShadow = 'none';
            }});
            
            // Change link colors to dark gray
            svgClone.querySelectorAll('.link').forEach(link => {{
                link.setAttribute('stroke', '#666666');
            }});
            
            // Serialize modified SVG to string
            const serializer = new XMLSerializer();
            let svgString = serializer.serializeToString(svgClone);
            
            // Create a blob and convert to data URL
            const blob = new Blob([svgString], {{ type: 'image/svg+xml;charset=utf-8' }});
            const url = URL.createObjectURL(blob);
            
            // Load SVG as image
            const img = new Image();
            img.onload = function() {{
                // Draw with transform applied
                ctx.save();
                ctx.translate(padding - bbox.x, padding - bbox.y);
                ctx.drawImage(img, 0, 0);
                ctx.restore();
                
                // Convert to PNG and download
                canvas.toBlob(function(blob) {{
                    const link = document.createElement('a');
                    link.download = 'network-topology.png';
                    link.href = URL.createObjectURL(blob);
                    link.click();
                    URL.revokeObjectURL(url);
                }});
            }};
            img.src = url;
        }}
    </script>
</body>
</html>"""
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        return output_file
    
    def generate_static_svg(self, output_file: str = 'network_topology.svg'):
        """
        Generate a static SVG diagram (alternative to interactive HTML)
        
        Args:
            output_file: Path to output SVG file
        """
        self.generate_graph_data()
        
        # Simple grid layout for static SVG
        import math
        
        n_nodes = len(self.nodes)
        cols = math.ceil(math.sqrt(n_nodes))
        
        width = 1200
        height = 800
        margin = 100
        
        node_positions = {}
        for i, node in enumerate(self.nodes):
            row = i // cols
            col = i % cols
            x = margin + (width - 2 * margin) * col / max(1, cols - 1) if cols > 1 else width / 2
            y = margin + (height - 2 * margin) * row / max(1, math.ceil(n_nodes / cols) - 1)
            node_positions[node['id']] = (x, y)
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
    <rect width="{width}" height="{height}" fill="#0d1117"/>
    
    <!-- Links -->
'''
        
        # Draw edges
        for edge in self.edges:
            x1, y1 = node_positions[edge['source']]
            x2, y2 = node_positions[edge['target']]
            
            svg_content += f'    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#999" stroke-width="2"/>\n'
            
            # Interface labels
            mid_x1, mid_y1 = x1 + (x2 - x1) * 0.25, y1 + (y2 - y1) * 0.25
            mid_x2, mid_y2 = x1 + (x2 - x1) * 0.75, y1 + (y2 - y1) * 0.75
            
            svg_content += f'    <text x="{mid_x1}" y="{mid_y1}" fill="#FFE66D" font-size="10" text-anchor="middle">{edge["local_interface"]}</text>\n'
            svg_content += f'    <text x="{mid_x2}" y="{mid_y2}" fill="#FFE66D" font-size="10" text-anchor="middle">{edge["remote_interface"]}</text>\n'
        
        svg_content += '    \n    <!-- Nodes -->\n'
        
        # Draw nodes
        for node in self.nodes:
            x, y = node_positions[node['id']]
            color = node['color']
            
            svg_content += f'    <circle cx="{x}" cy="{y}" r="25" fill="{color}" stroke="#fff" stroke-width="2"/>\n'
            svg_content += f'    <text x="{x}" y="{y + 40}" fill="#fff" font-size="12" text-anchor="middle" font-weight="bold">{node["label"]}</text>\n'
        
        svg_content += '</svg>'
        
        with open(output_file, 'w') as f:
            f.write(svg_content)
        
        return output_file
