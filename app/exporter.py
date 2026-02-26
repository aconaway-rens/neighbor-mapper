"""
Export and reporting module for Network Neighbor Mapper
Generates JSON, CSV, and PDF exports of discovered topology data
"""

import csv
import html
import io
import json
from datetime import datetime

import weasyprint


def topology_to_dict(topology, seed_ip=None, params=None):
    """
    Serialize a Topology object to a plain dict.

    Args:
        topology: Topology object from discovery.py
        seed_ip: Seed device IP address used for this discovery
        params: Dict of discovery parameters (max_depth, filters, etc.)

    Returns:
        Serializable dict
    """
    devices = []
    for hostname, device in topology.devices.items():
        devices.append({
            'hostname': hostname,
            'mgmt_ip': device.mgmt_ip,
            'device_type': device.device_type,
            'device_category': device.device_category,
            'has_routing': device.has_routing,
            'platform': device.platform,
            'arp_entries': device.arp_entries if device.arp_entries else [],
        })

    links = []
    seen = set()
    for device in topology.devices.values():
        for link in device.links:
            key = tuple(sorted([
                f"{link.local_device}:{link.local_intf}",
                f"{link.remote_device}:{link.remote_intf}"
            ]))
            if key in seen:
                continue
            seen.add(key)
            links.append({
                'local_device': link.local_device,
                'local_interface': link.local_intf,
                'remote_device': link.remote_device,
                'remote_interface': link.remote_intf,
                'remote_ip': link.remote_ip,
                'protocols': '+'.join(link.protocols) if link.protocols else '',
            })

    return {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'seed_ip': seed_ip,
        'params': params or {},
        'summary': {
            'device_count': len(devices),
            'link_count': len(links),
        },
        'devices': devices,
        'links': links,
    }


def generate_json(data):
    """Return topology data as a formatted JSON string."""
    return json.dumps(data, indent=2)


def generate_csv(data):
    """
    Return topology data as a single CSV string with two sections:
    a Devices block followed by a blank line and a Links block.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # --- Devices section ---
    writer.writerow(['DEVICES'])
    writer.writerow(['Hostname', 'Management IP', 'Category', 'Device Type', 'Has Routing', 'Platform'])
    for device in data.get('devices', []):
        writer.writerow([
            device.get('hostname', ''),
            device.get('mgmt_ip', ''),
            device.get('device_category', ''),
            device.get('device_type', ''),
            'Yes' if device.get('has_routing') else 'No',
            device.get('platform', ''),
        ])

    # Blank separator row
    writer.writerow([])

    # --- Links section ---
    writer.writerow(['LINKS'])
    writer.writerow(['Local Device', 'Local Interface', 'Remote Device', 'Remote Interface', 'Remote IP', 'Protocols'])
    for link in data.get('links', []):
        writer.writerow([
            link.get('local_device', ''),
            link.get('local_interface', ''),
            link.get('remote_device', ''),
            link.get('remote_interface', ''),
            link.get('remote_ip', ''),
            link.get('protocols', ''),
        ])

    # --- ARP section (only if any device has ARP entries) ---
    arp_devices = [d for d in data.get('devices', []) if d.get('arp_entries')]
    if arp_devices:
        writer.writerow([])
        writer.writerow(['ARP ENTRIES'])
        writer.writerow(['Device', 'Interface', 'IP', 'MAC', 'Age'])
        for device in arp_devices:
            hostname = device.get('hostname', '')
            for entry in device.get('arp_entries', []):
                writer.writerow([
                    hostname,
                    entry.get('interface', ''),
                    entry.get('ip', ''),
                    entry.get('mac', ''),
                    entry.get('age', ''),
                ])

    return output.getvalue()


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------

_CATEGORY_BADGE = {
    'router':   ('badge-router',   'Router'),
    'switch':   ('badge-switch',   'Switch'),
    'l3switch': ('badge-switch',   'L3 Switch'),
    'firewall': ('badge-firewall', 'Firewall'),
    'ap':       ('badge-ap',       'AP'),
    'wireless': ('badge-ap',       'Wireless'),
    'phone':    ('badge-phone',    'Phone'),
    'server':   ('badge-server',   'Server'),
}

_PDF_CSS = """
@page {
    size: letter;
    margin: 0.75in;
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 8pt;
        color: #888;
    }
}

body {
    font-family: Liberation Sans, Arial, sans-serif;
    font-size: 10pt;
    color: #222;
    line-height: 1.45;
}

.report-header {
    border-bottom: 3px solid #667eea;
    padding-bottom: 10pt;
    margin-bottom: 18pt;
}

h1 {
    font-size: 20pt;
    color: #667eea;
    margin: 0 0 4pt 0;
    font-weight: bold;
}

.meta {
    font-size: 8.5pt;
    color: #666;
}

h2 {
    font-size: 13pt;
    color: #667eea;
    border-bottom: 1px solid #d8dcff;
    padding-bottom: 3pt;
    margin-top: 22pt;
    margin-bottom: 10pt;
    font-weight: bold;
}

/* Summary stat boxes */
.summary-grid {
    display: flex;
    gap: 12pt;
    margin-bottom: 6pt;
}

.stat-box {
    flex: 1;
    background: #f4f5ff;
    border: 1px solid #c8ccf5;
    border-radius: 4pt;
    padding: 10pt 14pt;
    text-align: center;
}

.stat-value {
    font-size: 24pt;
    font-weight: bold;
    color: #667eea;
    line-height: 1.1;
}

.stat-label {
    font-size: 8pt;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.4pt;
    margin-top: 2pt;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 9pt;
    margin-bottom: 10pt;
}

thead th {
    background: #667eea;
    color: white;
    padding: 6pt 8pt;
    text-align: left;
    font-weight: bold;
}

tbody td {
    padding: 5pt 8pt;
    border-bottom: 1px solid #eaebf5;
    vertical-align: top;
}

tbody tr:nth-child(even) td {
    background: #f8f8ff;
}

/* Link section group header row */
.group-row td {
    background: #eef0ff !important;
    font-weight: bold;
    color: #444;
    border-top: 2px solid #c8ccf5;
    font-size: 9.5pt;
    padding: 5pt 8pt;
}

/* Category badges */
.badge {
    display: inline-block;
    padding: 1pt 6pt;
    border-radius: 3pt;
    font-size: 7.5pt;
    font-weight: bold;
    text-transform: uppercase;
}

.badge-router   { background: #fde8e8; color: #b03020; }
.badge-switch   { background: #e3f0fd; color: #1a6fa8; }
.badge-firewall { background: #fef5e0; color: #b85c00; }
.badge-ap       { background: #e3fdf0; color: #1a8050; }
.badge-phone    { background: #f0e8fd; color: #6030a0; }
.badge-server   { background: #e8f8e8; color: #207020; }
.badge-other    { background: #f0f0f0; color: #555; }

/* Protocol tag */
.proto {
    display: inline-block;
    padding: 1pt 5pt;
    border-radius: 2pt;
    background: #ede8ff;
    color: #5533aa;
    font-size: 7.5pt;
    font-weight: bold;
}
"""


def _esc(value):
    """HTML-escape a value, returning empty string for None."""
    return html.escape(str(value)) if value else ''


def _category_badge(cat):
    cat_lower = (cat or '').lower()
    css_cls, label = _CATEGORY_BADGE.get(cat_lower, ('badge-other', cat or 'Unknown'))
    return f'<span class="badge {css_cls}">{_esc(label)}</span>'


def _build_pdf_html(data):
    """Build the complete HTML string for the PDF report."""
    seed_ip = data.get('seed_ip', 'Unknown')
    generated_at = data.get('generated_at', '')
    params = data.get('params', {})
    summary = data.get('summary', {})
    devices = data.get('devices', [])
    links = data.get('links', [])

    max_depth = params.get('max_depth', '')
    failed_count = params.get('failed_count', 0)

    # --- Meta line ---
    meta_parts = [f'Seed: {_esc(seed_ip)}', f'Generated: {_esc(generated_at)}']
    if max_depth:
        meta_parts.append(f'Max Depth: {_esc(str(max_depth))}')
    meta_html = ' &nbsp;·&nbsp; '.join(meta_parts)

    # --- Summary stat boxes ---
    failed_box = ''
    if failed_count:
        failed_box = (
            f'<div class="stat-box">'
            f'<div class="stat-value">{failed_count}</div>'
            f'<div class="stat-label">Failed</div>'
            f'</div>'
        )
    summary_html = (
        f'<div class="summary-grid">'
        f'<div class="stat-box">'
        f'<div class="stat-value">{summary.get("device_count", 0)}</div>'
        f'<div class="stat-label">Devices</div>'
        f'</div>'
        f'<div class="stat-box">'
        f'<div class="stat-value">{summary.get("link_count", 0)}</div>'
        f'<div class="stat-label">Links</div>'
        f'</div>'
        f'{failed_box}'
        f'</div>'
    )

    # --- Device inventory table ---
    if devices:
        device_rows = ''
        for d in devices:
            device_rows += (
                f'<tr>'
                f'<td><strong>{_esc(d.get("hostname", ""))}</strong></td>'
                f'<td>{_esc(d.get("mgmt_ip", ""))}</td>'
                f'<td>{_category_badge(d.get("device_category", ""))}</td>'
                f'<td>{_esc(d.get("device_type", ""))}</td>'
                f'<td>{_esc(d.get("platform", ""))}</td>'
                f'</tr>'
            )
        device_section = (
            f'<table>'
            f'<thead><tr>'
            f'<th>Hostname</th><th>Mgmt IP</th><th>Category</th>'
            f'<th>Device Type</th><th>Platform</th>'
            f'</tr></thead>'
            f'<tbody>{device_rows}</tbody>'
            f'</table>'
        )
    else:
        device_section = '<p>No devices found.</p>'

    # --- Link inventory table (grouped by local device) ---
    if links:
        # Group links by local device
        groups = {}
        for link in links:
            src = link.get('local_device', 'Unknown')
            groups.setdefault(src, []).append(link)

        link_rows = ''
        for src in sorted(groups.keys()):
            link_rows += (
                f'<tr class="group-row"><td colspan="5">{_esc(src)}</td></tr>'
            )
            for link in sorted(groups[src], key=lambda x: x.get('local_interface', '')):
                proto = link.get('protocols', '')
                proto_html = f'<span class="proto">{_esc(proto)}</span>' if proto else ''
                link_rows += (
                    f'<tr>'
                    f'<td>{_esc(link.get("local_interface", ""))}</td>'
                    f'<td>{_esc(link.get("remote_device", ""))}</td>'
                    f'<td>{_esc(link.get("remote_interface", ""))}</td>'
                    f'<td>{_esc(link.get("remote_ip", ""))}</td>'
                    f'<td>{proto_html}</td>'
                    f'</tr>'
                )
        link_section = (
            f'<table>'
            f'<thead><tr>'
            f'<th>Local Interface</th><th>Remote Device</th>'
            f'<th>Remote Interface</th><th>Remote IP</th><th>Protocols</th>'
            f'</tr></thead>'
            f'<tbody>{link_rows}</tbody>'
            f'</table>'
        )
    else:
        link_section = '<p>No links found.</p>'

    # --- ARP summary section (grouped by device + interface, count only) ---
    arp_devices = [d for d in devices if d.get('arp_entries')]
    if arp_devices:
        arp_rows = ''
        for d in arp_devices:
            hostname = d.get('hostname', '')
            # Group entries by interface
            by_intf = {}
            for entry in d.get('arp_entries', []):
                intf = entry.get('interface') or 'Unknown'
                by_intf[intf] = by_intf.get(intf, 0) + 1
            # Sort VLANs numerically, then alphabetically
            def _intf_sort_key(name):
                import re as _re
                m = _re.match(r'^[Vv]lan(\d+)$', name)
                return (0, int(m.group(1))) if m else (1, name)
            first = True
            for intf in sorted(by_intf.keys(), key=_intf_sort_key):
                arp_rows += (
                    f'<tr>'
                    f'<td>{"<strong>" + _esc(hostname) + "</strong>" if first else ""}</td>'
                    f'<td>{_esc(intf)}</td>'
                    f'<td style="text-align:right">{by_intf[intf]}</td>'
                    f'</tr>'
                )
                first = False
        arp_section = (
            f'<table>'
            f'<thead><tr>'
            f'<th>Device</th><th>Interface</th><th style="text-align:right">ARP Entries</th>'
            f'</tr></thead>'
            f'<tbody>{arp_rows}</tbody>'
            f'</table>'
            f'<p style="font-size:8pt;color:#888">Full ARP entry detail is available in the CSV export.</p>'
        )
    else:
        arp_section = None

    arp_html = f'\n<h2>ARP Summary</h2>\n{arp_section}' if arp_section else ''

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{_PDF_CSS}</style>
</head>
<body>

<div class="report-header">
  <h1>Network Topology Report</h1>
  <div class="meta">{meta_html}</div>
</div>

<h2>Summary</h2>
{summary_html}

<h2>Device Inventory</h2>
{device_section}

<h2>Link Inventory</h2>
{link_section}{arp_html}

</body>
</html>"""


def generate_pdf(data):
    """Return topology data as a PDF (bytes) using WeasyPrint."""
    html_source = _build_pdf_html(data)
    return weasyprint.HTML(string=html_source).write_pdf()
