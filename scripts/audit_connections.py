#!/usr/bin/env python3
"""Read-only dashboard entity/service audit. Never calls a device service.

Use --states /private/path/states.json and --services /private/path/services.json,
or set HA_URL and HA_TOKEN in the environment for authenticated REST GETs.
Reports IDs/statuses only; does not print tokens or entity attributes.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = 'alarm_control_panel binary_sensor button camera climate cover device_tracker input_boolean input_select light lock media_player number person remote scene script select sensor sun switch update vacuum weather zone'.split()
ENTITY = re.compile(r'\b(?:' + '|'.join(DOMAINS) + r')\.[a-z0-9_]+\b')


def references(doc):
    entities, services = set(), set()
    def visit(value, key=''):
        if isinstance(value, dict):
            for k, v in value.items():
                visit(v, k)
        elif isinstance(value, list):
            for v in value:
                visit(v, key)
        elif isinstance(value, str):
            if key in ('service', 'perform_action') and '[[[' not in value:
                services.add(value)
            elif key not in ('navigation_path', 'url', 'icon'):
                if '[[[' in value or "states[" in value:
                    # Only quoted IDs; ignore JavaScript variables such as sun.state.
                    for match in re.finditer(r"[\"'](" + ENTITY.pattern + r")[\"']", value):
                        eid = match.group(1)
                        if not eid.endswith('.unknown'):
                            entities.add(eid)
                else:
                    entities.update(ENTITY.findall(value))
    visit(doc)
    return entities, services


def active_dashboard(doc, view_paths=None):
    """Include only templates used by the selected views, including inheritance."""
    templates = doc.get('button_card_templates', {})
    views = [v for v in doc.get('views', []) if not view_paths or v.get('path') in view_paths]
    used = {}
    def visit(node):
        if isinstance(node, dict):
            names = node.get('template', [])
            if isinstance(names, str): names = [names]
            for name in names if isinstance(names, list) else []:
                if name in templates and name not in used:
                    used[name] = templates[name]
                    visit(templates[name])
            for value in node.values(): visit(value)
        elif isinstance(node, list):
            for value in node: visit(value)
    visit(views)
    return {'views': views, 'button_card_templates': used}


def audit(entities, services, states, available_services=None):
    live = {s['entity_id']: s['state'] for s in states}
    result = {'missing': [], 'unavailable': [], 'unknown': [], 'present': [], 'missing_services': []}
    for eid in sorted(entities):
        status = 'missing' if eid not in live else live[eid] if live[eid] in ('unknown', 'unavailable') else 'present'
        result[status].append(eid)
    if available_services is not None:
        known = {f"{domain['domain']}.{service}" for domain in available_services for service in domain['services']}
        result['missing_services'] = sorted(services - known)
    result['services_checked'] = available_services is not None
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--states', type=Path)
    parser.add_argument('--services', type=Path)
    parser.add_argument('--dashboard', type=Path, help='Audit generated/deployed dashboard instead of source views/templates')
    parser.add_argument('--views', help='Comma-separated paths to audit, excluding archived or unused pages')
    args = parser.parse_args()
    files = [args.dashboard] if args.dashboard else sorted((ROOT/'views').glob('*.yaml')) + sorted((ROOT/'templates').glob('*.yaml'))
    entities, services = set(), set()
    for file in files:
        doc = yaml.safe_load(file.read_text())
        if args.dashboard:
            doc = active_dashboard(doc, args.views.split(',') if args.views else None)
        e, s = references(doc)
        entities.update(e); services.update(s)
    if args.states:
        states = json.loads(args.states.read_text())
        available = json.loads(args.services.read_text()) if args.services else None
    elif os.environ.get('HA_URL') and os.environ.get('HA_TOKEN'):
        def get(path):
            request = urllib.request.Request(os.environ['HA_URL'].rstrip('/') + path, headers={'Authorization': 'Bearer ' + os.environ['HA_TOKEN']})
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        states, available = get('/api/states'), get('/api/services')
    else:
        print(json.dumps({'live_verified': False, 'entity_references': sorted(entities), 'service_references': sorted(services)}, indent=2))
        return 2
    report = audit(entities, services, states, available)
    print(json.dumps(report, indent=2))
    return int(any(report[key] for key in ('missing', 'unavailable', 'unknown', 'missing_services')))


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'Audit could not complete ({type(exc).__name__}); check connection and input files.', file=sys.stderr)
        sys.exit(2)
