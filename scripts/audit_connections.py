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
                entities.update(ENTITY.findall(value))
    visit(doc)
    return entities, services


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
    args = parser.parse_args()
    files = [args.dashboard] if args.dashboard else sorted((ROOT/'views').glob('*.yaml')) + sorted((ROOT/'templates').glob('*.yaml'))
    entities, services = set(), set()
    for file in files:
        e, s = references(yaml.safe_load(file.read_text()))
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
