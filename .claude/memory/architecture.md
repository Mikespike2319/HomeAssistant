# Architecture — single VPS, Docker-composed

Everything runs on this VPS. There is no remote home box.

## Containers (from `docker ps`)

| Container | Image | Role |
|---|---|---|
| `homeassistant` | `ghcr.io/home-assistant/home-assistant:stable` | Home Assistant — primary brain. Config bind-mount: `/opt/ha-vps/homeassistant/` ↔ `/config` inside container. |
| `nodered` | `nodered/node-red:latest` | Node-RED automations (port 1880, internal) |
| `grafana` | `grafana/grafana:latest` | Dashboards on top of InfluxDB |
| `influxdb` | `influxdb:1.8` | Time-series storage for HA history |
| `traefik` | `traefik:v2.11` | Public-facing reverse proxy on :80/:443. Routes to subdomains. |

## File layout

| Path | Purpose |
|---|---|
| `/opt/ha-vps/homeassistant/` | HA config root (mounted as `/config` in container) |
| `/opt/ha-vps/homeassistant/configuration.yaml` | Main HA config — Lovelace mode: `storage`, with named dashboards including `mobile-forge` |
| `/opt/ha-vps/homeassistant/dashboards/mobile_forge v5.yaml` | The active Mobile Forge dashboard (note the space in the filename) |
| `/opt/ha-vps/homeassistant/dashboards/command_center.yaml` | Wide-screen Command Center dashboard |
| `/opt/ha-vps/homeassistant/dashboards/trips.yaml` | Travel/trips dashboard |
| `/opt/ha-vps/homeassistant/custom_components/` | HACS-installed integrations |
| `/opt/ha-vps/homeassistant/themes/` | Custom themes (loaded via `frontend.themes: !include_dir_merge_named themes`) |
| `/root/HomeAssistant/` | **Source-of-truth dashboard repo.** Edit here first, then deploy. Has its own git history. |
| `/root/HomeAssistant/views/*.yaml` | One file per Mobile Forge view (house, lights, music, security, tesla, weather) |
| `/root/HomeAssistant/templates/*.yaml` | Reusable button-card templates (sky_system, cozy_*, tesla_tap_zone) |
| `/root/HomeAssistant/scripts/` | Python deploy helpers |
| `/root/HomeAssistant/INSTALL/` | Newer deploy scripts: `deploy.py`, `merge_into_mobile_forge.py`, `replace_home_view.py` |

## Two Lovelace dashboards both live here

`configuration.yaml` declares three YAML-mode dashboards: `command-center`, `mobile-forge`, `my-trips`. Storage-mode dashboards also exist (default Overview). Mobile Forge is the iOS-companion target.

## Network paths

- HA UI: `http://localhost:8123` (Docker `homeassistant` container, host-network or port-mapped — verify with `docker inspect homeassistant`)
- Mobile Forge URL: `<HA-URL>/mobile-forge/home`
- Traefik handles public TLS — never expose HA's `:8123` directly past Traefik. Anything HA-adjacent (HA-MCP, webhooks) stays internal.

## Why backups are everywhere

`/opt/ha-vps/homeassistant/` is full of `.bak-*-YYYYMMDD-HHMMSS` and `.before-*-YYYYMMDD-HHMMSS` files. Past sessions made risky edits and saved escape hatches. The naming convention `<name>.<reason>-<timestamp>` is followed — keep using it when overwriting things.

## Source-of-truth contract

The `/root/HomeAssistant/` repo is canonical. The deployed YAML at `/opt/ha-vps/homeassistant/dashboards/mobile_forge v5.yaml` is generated from it. If you edit the deployed file directly without mirroring back, the next deploy will clobber the change.
