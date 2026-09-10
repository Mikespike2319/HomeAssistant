import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import install_wife_approved_mobile_forge as installer
from audit_connections import audit, references


def evaluate(expression, entity=None):
    js = 'const entity = ' + json.dumps(entity) + '; const variables = {}; const states = {}; console.log(JSON.stringify((function(){' + expression.strip()[3:-3] + '})()));'
    return json.loads(subprocess.check_output(['node', '-e', js], text=True))


class DashboardTests(unittest.TestCase):
    def test_home_missing_devices_do_not_claim_health(self):
        with tempfile.TemporaryDirectory() as directory:
            cards = installer.make_home_cards(Path(directory), None)
        self.assertEqual(cards[0]['template'], 'sky_system')
        self.assertEqual(evaluate(cards[2]['variables']['value']), 'No reading')
        for card in cards[3]['cards']:
            self.assertIn(evaluate(card['variables']['value']), ['Not connected', 'Not available'])
        self.assertEqual(cards[3]['cards'][1]['entity'], 'light.living_room')
        self.assertEqual(evaluate(cards[3]['cards'][0]['variables']['value'], {'state':'0'}), '0%')
        for card in cards[4]['cards']:
            self.assertEqual(card['tap_action']['target']['entity_id'], card['entity'])
            self.assertEqual(evaluate(card['tap_action']['action']), 'more-info')
            self.assertEqual(evaluate(card['tap_action']['action'], {'state':'2026-09-10T12:00:00Z'}), 'call-service')

    def test_audit_distinguishes_missing_offline_and_off(self):
        entities, services = references({'entity':'light.room', 'tap_action':{'service':'light.turn_on', 'target':{'entity_id':['light.offline', 'light.missing']}}, 'value':"states['sensor.test']"})
        report = audit(entities, services, [{'entity_id':'light.room','state':'off'}, {'entity_id':'light.offline','state':'unavailable'}, {'entity_id':'sensor.test','state':'unknown'}], [{'domain':'light','services':{'turn_on':{}}}])
        self.assertEqual(report['present'], ['light.room'])
        self.assertEqual(report['missing'], ['light.missing'])
        self.assertEqual(report['unavailable'], ['light.offline'])
        self.assertEqual(report['unknown'], ['sensor.test'])
        self.assertEqual(report['missing_services'], [])

    def test_yaml_and_javascript_parse(self):
        scripts=[]
        def visit(v):
            if isinstance(v, dict):
                for child in v.values(): visit(child)
            elif isinstance(v, list):
                for child in v: visit(child)
            elif isinstance(v, str) and v.strip().startswith('[[[') and v.strip().endswith(']]]'):
                scripts.append(v.strip()[3:-3])
        for file in list((ROOT/'templates').glob('*.yaml')) + list((ROOT/'views').glob('*.yaml')):
            visit(yaml.safe_load(file.read_text()))
        check = 'const fs=require("fs"); for(const source of JSON.parse(fs.readFileSync(0,"utf8"))) new Function("entity","states","variables",source);'
        subprocess.run(['node','-e',check], input=json.dumps(scripts), text=True, check=True)

    def test_installer_preserves_other_views_and_is_repeatable(self):
        dashboard = yaml.safe_load((ROOT/'deployed_snapshot/mobile_forge_v5.yaml').read_text())
        unaffected = copy.deepcopy([v for v in dashboard['views'] if v['path'] not in ['home','lights','media','house','tesla','security','music','forge-classic']])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'configuration.yaml').write_text('automation: !include automations.yaml\nhttp:\n  password: !secret ignored\nlovelace:\n  dashboards:\n    mobile-forge:\n      mode: yaml\n      filename: dashboard.yaml\n')
            target = root/'dashboard.yaml'
            target.write_text(yaml.safe_dump(dashboard))
            classic_before = None
            for _ in range(2):
                subprocess.run([sys.executable,str(ROOT/'scripts/install_wife_approved_mobile_forge.py'),'--config-dir',str(root)], stdout=subprocess.DEVNULL, check=True)
                current = yaml.safe_load(target.read_text())
                classic = next(v for v in current['views'] if v['path'] == 'forge-classic')
                if classic_before is not None:
                    self.assertEqual(classic_before, classic)
                classic_before = copy.deepcopy(classic)
            result = yaml.safe_load(target.read_text())
            self.assertEqual(unaffected, [v for v in result['views'] if v['path'] not in ['home','lights','media','house','tesla','security','music','forge-classic']])
            paths = [v['path'] for v in result['views']]
            self.assertEqual(len(paths), len(set(paths)))
            installer.assert_integrity(result)

if __name__ == '__main__':
    unittest.main()
