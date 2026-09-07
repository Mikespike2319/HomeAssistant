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
- Mode: YAML (file-driven, edits to that file = live changes after restart)

## Apply changes after editing

Safest one-shot installer on the VPS. This updates the active Home view and
syncs the redesigned Lights, Media, Tesla, Security, House, and Weather views:

```bash
python3 scripts/install_wife_approved_mobile_forge.py --config-dir /opt/ha-vps/homeassistant --dry-run
python3 scripts/install_wife_approved_mobile_forge.py --config-dir /opt/ha-vps/homeassistant
```

After deploying Lovelace-only changes, refresh the dashboard or reload
Lovelace resources. A Home Assistant container restart is not required.

## Important

The active Mobile Forge Home view should start with:

```yaml
type: custom:button-card
template: sky_system
```

`sky_system_tesla` remains available for experiments, but production views use
the asset-free `sky_system` template. It reacts to day/night and storm state,
honors reduced-motion preferences, and stays behind interactive cards.
