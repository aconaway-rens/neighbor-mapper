from netmiko import ( ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException, )
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List
from flask import Flask, render_template_string, request
import logging
from jinja2 import Environment, FileSystemLoader
import os

LOG_PATH = "/app/logs/app.log"
TEMPLATES_DIR = "/app/templates/"

logging.basicConfig( 
    filename=LOG_PATH, 
    level=logging.DEBUG, 
    format="%(asctime)s [%(levelname)s] %(message)s", ) 
logger = logging.getLogger(__name__)

@dataclass
class Link:
    local_device: str
    local_intf: str
    remote_device: str
    remote_intf: str
    protocol: str  # "CDP" or "LLDP"

@dataclass
class Device:
    hostname: str
    mgmt_ip: str
    platform: str | None = None
    links: List[Link] = field(default_factory=list)

@dataclass
class Topology:
    devices: Dict[str, Device] = field(default_factory=dict)

    def add_link(self, link: Link):
        for dev_name, ip in [(link.local_device, None), (link.remote_device, None)]:
            if dev_name not in self.devices:
                self.devices[dev_name] = Device(hostname=dev_name, mgmt_ip=ip)
        self.devices[link.local_device].links.append(link)

@dataclass
class DiscoveryResult:
    def __init__(self, topo=None, error=None):
        self.topo = topo
        self.error = error

@dataclass
class DiscoveryError(Exception):
    def __init__(self, message, kind):
        super().__init__(message)
        self.kind = kind # "timeout", "auth", "generic" 
        self.message = message



def connect_device(host, device_type, username, password):
    return ConnectHandler(
        device_type=device_type,
        host=host,
        username=username,
        password=password,
        fast_cli=True,
    )

def try_connect(host, device_type, username, password): 
    try: 
        return ConnectHandler( device_type=device_type, host=host, username=username, password=password, fast_cli=True, ) 
    except NetmikoTimeoutException: 
        logger.debug(f"Timed out connecting to {host}.")
        raise DiscoveryError( f"Connection to {host} timed out. The device may be offline or unreachable.", kind="timeout", ) 
    except NetmikoAuthenticationException: 
        raise DiscoveryError( f"Authentication failed when connecting to {host}. Check username/password.", kind="auth", ) 
    except Exception as e: 
        raise DiscoveryError( f"Unexpected error connecting to {host}: {e}", kind="generic", )

def parse_cdp_neighbors_detail(output: str):
    # TODO: robust parsing; this is just a sketch
    neighbors = []
    current = {}
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Device ID:"):
            if current:
                neighbors.append(current)
                current = {}
            current["remote_device"] = line.split("Device ID:")[1].strip()
        elif line.startswith("IP address:"):
            current["remote_ip"] = line.split("IP address:")[1].strip()
        elif line.startswith("Interface:"):
            parts = line.split(",")
            local_intf = parts[0].split("Interface:")[1].strip()
            remote_intf = parts[1].split("Port ID (outgoing port):")[1].strip()
            current["local_intf"] = local_intf
            current["remote_intf"] = remote_intf
    if current:
        neighbors.append(current)
    return neighbors

def parse_lldp_neighbors_detail(output: str):
    # Similar idea; vendor-specific parsing needed
    return []

def discover_topology(seed_host, device_type, username, password, max_depth=5):
    topo = Topology()
    visited = set()
    queue = deque([(seed_host, 0)])

    while queue:
        host, depth = queue.popleft()
        if depth > max_depth or host in visited:
            continue
        visited.add(host)

        try: 
            conn = try_connect(seed_host, device_type, username, password) 
        except DiscoveryError as e: 
            return DiscoveryResult(topo=None, error=e.message)

        hostname = conn.find_prompt().strip("#>").strip()
        if hostname not in topo.devices:
            topo.devices[hostname] = Device(hostname=hostname, mgmt_ip=host)

        # CDP
        try:
            cdp_out = conn.send_command("show cdp neighbors detail")
            cdp_neighbors = parse_cdp_neighbors_detail(cdp_out)
        except Exception:
            cdp_neighbors = []

        # LLDP
        try:
            lldp_out = conn.send_command("show lldp neighbors detail")
            lldp_neighbors = parse_lldp_neighbors_detail(lldp_out)
        except Exception:
            lldp_neighbors = []

        for n in cdp_neighbors:
            link = Link(
                local_device=hostname,
                local_intf=n["local_intf"],
                remote_device=n["remote_device"],
                remote_intf=n.get("remote_intf", "?"),
                protocol="CDP",
            )
            topo.add_link(link)
            if n.get("remote_ip"):
                queue.append((n["remote_ip"], depth + 1))

        # Add LLDP neighbors similarly...

        conn.disconnect()
        return DiscoveryResult(topo=topo, error=None)

    return topo

def build_adjacency(topo: Topology):
    adj = {}
    for dev in topo.devices.values():
        adj.setdefault(dev.hostname, set())
        for link in dev.links:
            adj[link.local_device].add(link.remote_device)
            adj.setdefault(link.remote_device, set()).add(link.local_device)
    return adj

def render_text_topology(topo: Topology, root: str | None = None) -> str:
    # if hostname not in topo.devices:
    #     topo.devices[host] = Device(hostname=host, mgmt_ip=host)
    adj = build_adjacency(topo)
    if not adj:
         return "Discovery succeeded, but no neighbors were found."

    if root is None:
        root = next(iter(adj))

    adj = build_adjacency(topo)
    if root is None:
        root = next(iter(adj))  # pick any

    lines = []
    visited = set()

    def dfs(node, prefix=""):
        visited.add(node)
        neighbors = sorted(adj[node] - visited)
        for i, nbr in enumerate(neighbors):
            is_last = i == len(neighbors) - 1
            connector = "└─" if is_last else "├─"
            lines.append(f"{prefix}{connector} {nbr}")
            new_prefix = prefix + ("   " if is_last else "│  ")
            dfs(nbr, new_prefix)

    lines.append(root)
    dfs(root)
    return "\n".join(lines)



app = Flask(__name__)

environment = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
root_template = environment.get_template("root.j2")
TEMPLATE = root_template.render()

@app.route("/", methods=["GET", "POST"])
def index():
    logger.debug("Started the / route")
    topo_text = None
    error_msg = None

    if request.method == "POST":
        seed = request.form["seed"]
        username = request.form["username"]
        password = request.form["password"]
        device_type = request.form['device_type']

        result = discover_topology(seed, device_type, username, password)

        if result.error:
            error_msg = result.error
        else:
            topo_text = render_text_topology(result.topo)

    return render_template_string(TEMPLATE, topology=topo_text, error=error_msg)



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
