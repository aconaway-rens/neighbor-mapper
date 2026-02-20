"""
Export and reporting module for Network Neighbor Mapper
Generates JSON, CSV, and PDF exports of discovered topology data
"""

import io
import csv
import json
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer


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

    return output.getvalue()


def generate_pdf(data):
    """
    Return topology data as a PDF (bytes) using reportlab.
    Includes a header, summary stats, device table, and link table.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=6,
    )
    normal_style = styles['Normal']

    elements = []

    # --- Title and metadata ---
    elements.append(Paragraph('Network Topology Report', title_style))
    elements.append(Spacer(1, 4))

    seed_ip = data.get('seed_ip', 'Unknown')
    generated_at = data.get('generated_at', '')
    elements.append(Paragraph(f'Seed Device: {seed_ip}', normal_style))
    elements.append(Paragraph(f'Generated: {generated_at}', normal_style))

    params = data.get('params', {})
    if params:
        max_depth = params.get('max_depth', '')
        if max_depth:
            elements.append(Paragraph(f'Max Discovery Depth: {max_depth}', normal_style))

    elements.append(Spacer(1, 12))

    # --- Summary stats ---
    elements.append(Paragraph('Summary', heading_style))
    summary = data.get('summary', {})
    summary_table_data = [
        ['Metric', 'Value'],
        ['Devices Discovered', str(summary.get('device_count', 0))],
        ['Links Found', str(summary.get('link_count', 0))],
    ]
    failed_count = params.get('failed_count', 0)
    if failed_count:
        summary_table_data.append(['Failed Connections', str(failed_count)])

    summary_table = Table(summary_table_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(summary_table)

    # --- Device inventory ---
    elements.append(Paragraph('Device Inventory', heading_style))
    devices = data.get('devices', [])
    if devices:
        device_table_data = [['Hostname', 'Management IP', 'Category', 'Device Type', 'Platform']]
        for device in devices:
            device_table_data.append([
                device.get('hostname', ''),
                device.get('mgmt_ip', '') or '',
                device.get('device_category', '') or '',
                device.get('device_type', '') or '',
                device.get('platform', '') or '',
            ])
        col_widths = [1.8 * inch, 1.2 * inch, 1.0 * inch, 1.2 * inch, 1.8 * inch]
        device_table = Table(device_table_data, colWidths=col_widths, repeatRows=1)
        device_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        elements.append(device_table)
    else:
        elements.append(Paragraph('No devices found.', normal_style))

    # --- Link inventory ---
    elements.append(Paragraph('Link Inventory', heading_style))
    links = data.get('links', [])
    if links:
        link_table_data = [['Local Device', 'Local Intf', 'Remote Device', 'Remote Intf', 'Remote IP', 'Protocols']]
        for link in links:
            link_table_data.append([
                link.get('local_device', ''),
                link.get('local_interface', ''),
                link.get('remote_device', ''),
                link.get('remote_interface', ''),
                link.get('remote_ip', '') or '',
                link.get('protocols', '') or '',
            ])
        col_widths = [1.4 * inch, 1.0 * inch, 1.4 * inch, 1.0 * inch, 1.0 * inch, 0.9 * inch]
        link_table = Table(link_table_data, colWidths=col_widths, repeatRows=1)
        link_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        elements.append(link_table)
    else:
        elements.append(Paragraph('No links found.', normal_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
