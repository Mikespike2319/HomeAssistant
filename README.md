# HearthOS — Mike & Kiara's Home Assistant

A mobile-first Home Assistant command deck for the Mobile Forge dashboard.
HearthOS combines a CSS-only animated aurora, state-aware glass controls,
Tesla "El Rocco" telemetry, Hue lighting, Blink security, weather, and
TV-first media controls. It has no remote background-image dependency.

## Layout

| Path | What |
|------|------|
| `deployed_snapshot/` | Snapshot of the live `mobile_forge v5.yaml` dashboard |
| `templates/` | All button-card templates (`sky_system`, `sky_system_tesla`, `cozy_*`) |
| `views/` | Individual view source files (Lights, Media, Music, Weather, etc.) |
| `assets/` | AI render prompts for Tesla Model Y 2026 art |
| `scripts/` | Python helpers: deploy, merge, replace_home |

## Live deploy paths

- HA config root: `/opt/ha-vps/homeassistant/`
- Active dashboard: `/opt/ha-vps/homeassistant/dashboards/mobile_forge v5.yaml`
- URL: `/mobile-forge/home`
- Mode: YAML (file-driven, edits to that file = live changes after a frontend refresh)

## Apply changes after editing

Safest one-shot installer on the VPS. This updates the active Home view
and syncs the Lights, Media, Music, House, Tesla, and Security source views:

```bash
python3 scripts/install_wife_approved_mobile_forge.py --config-dir /opt/ha-vps/homeassistant --dry-run
python3 scripts/install_wife_approved_mobile_forge.py --config-dir /opt/ha-vps/homeassistant
# Refresh the dashboard in your browser or Companion app
```

After manually editing the active YAML on the VPS:
```bash
# Refresh the dashboard in your browser or Companion app
```

## Important

The active Mobile Forge Home view should start with:

```yaml
type: custom:button-card
template: sky_system
```

`sky_system_tesla` remains available for Tesla-heavy pages, but the Reddit
Wife Approved animated weather background is now kept under the original
`sky_system` template name. The template z-indexes are lifted above the
Home Assistant page background so the sky is actually visible instead of
rendering behind the app shell.

## Connection checks and motion

Home shows unavailable/missing readings explicitly, and its scene shortcuts use
existing scene IDs from the Lights view. Those IDs still need checking against
the running instance. The read-only audit never invokes services:

```bash
# HA_URL and HA_TOKEN must already be set securely in your shell.
python3 scripts/audit_connections.py --dashboard "/opt/ha-vps/homeassistant/dashboards/mobile_forge v5.yaml"
# Or use private JSON exports of GET /api/states and GET /api/services:
python3 scripts/audit_connections.py --states /private/states.json --services /private/services.json
python3 -m unittest discover -s tests -v
```

Exit codes: 0 = referenced entities have known states and checked services exist;
1 = missing/unavailable/unknown references; 2 = no live input or incomplete audit.
A known entity state is not proof that a command physically works. TV standby
wake, scenes, camera streams, and integration authentication need live checks.
Source auditing includes optional/legacy templates; audit the active generated
dashboard for the references actually deployed. Dynamic entity expressions need
manual review. Keep exports and credentials outside this public repository.

The existing HTML preview uses **sample data**, not live connections. Card motion
uses brief entrances and press feedback. Reduced-motion preferences stop ambient
sky animation and card motion. The active sky is asset-free CSS. The legacy Tesla sky template still uses external local image assets.


The live VPS had a newer HearthOS revision than GitHub main. The current branch
includes that history and preserves its entity mappings and asset-free sky.
House now includes a connection status list for configured devices; Roomba setup
links to integrations until a vacuum is configured. Blink uses `blink_home` and
`camera.front_door`. The Home connection summary counts known states, not
successful physical commands or integration authentication.
