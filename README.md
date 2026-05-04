# Mike & Kiara — Home Assistant config

Cozy / Wife-Approved style Home Assistant dashboard for the Mobile
Forge dashboard. Animated sky_system backdrop + Tesla "El Rocco"
integration + Hue lights + Blink security + weather hero.

## Layout

| Path | What |
|------|------|
| `deployed_snapshot/` | Snapshot of the live `mobile_forge v5.yaml` dashboard |
| `templates/` | All button-card templates (sky_system + cozy_*) |
| `views/` | Individual view source files (Lights, Music, Weather, etc.) |
| `assets/` | AI render prompts for Tesla Model Y 2026 art |
| `scripts/` | Python helpers: deploy, merge, replace_home |

## Live deploy paths

- HA config root: `/opt/ha-vps/homeassistant/`
- Active dashboard: `/opt/ha-vps/homeassistant/dashboards/mobile_forge v5.yaml`
- URL: `/mobile-forge/home`
- Mode: YAML (file-driven, edits to that file = live changes after restart)

## Apply changes after editing

After editing the active YAML on the VPS:
```bash
docker restart homeassistant
```
