# Mike & Kiara — Home Assistant VPS Workspace

You are working on Michael's Home Assistant control-plane and Mobile Forge dashboard.
Home Assistant runs locally on this VPS in Docker (container `homeassistant`),
config root `/opt/ha-vps/homeassistant/`, active dashboard
`/opt/ha-vps/homeassistant/dashboards/mobile_forge v5.yaml`, served at `/mobile-forge/home`.

## Read these before making changes

- `.claude/memory/architecture.md` — how the pieces connect (HA, Node-RED, Grafana, Traefik, dashboard repo)
- `.claude/memory/dashboard-decisions.md` — Mobile Forge layout rules, iOS companion constraints, sky_system templating
- `.claude/memory/device-map.md` — entities, naming, integrations (Tesla "El Rocco", Hue, Blink, Sonos, Wyze, etc.)
- `.claude/memory/deploy-runbook.md` — apply-changes workflow (validate → backup → write → reload vs restart)
- `.claude/memory/common-errors.md` — recurring bugs and their fixes (Tesla image path, music tab regressions, iOS viewport)

## Hard rules

- **Validate YAML before saving** any file under `/opt/ha-vps/homeassistant/`. Use `docker exec homeassistant python -m homeassistant --script check_config -c /config` or `hass-cli config check` if available.
- **Backup or git-commit before risky changes.** The `.bak-uifix-YYYYMMDD-HHMMSS` files in `/opt/ha-vps/homeassistant/` are evidence of past bad days. Don't add to them.
- **Prefer reload over restart.** Lovelace/dashboard YAML reloads via the UI or `service: lovelace.reload_resources`. Templates and view changes only need a frontend refresh. Restart `homeassistant` container only when configuration.yaml itself changed.
- **Mobile-first.** The dashboard is consumed primarily on iOS via the HA Companion app. Don't introduce custom cards that break the iOS companion unless tested visually.
- **Never expose HA, MCP, tokens, or webhooks to the public internet.** Traefik is here for routing — anything HA-adjacent must stay on `localhost` or the internal Docker network.
- **Active home view starts with `type: custom:button-card` + `template: sky_system`.** Anything else means someone overwrote it. The Reddit "Wife Approved" animated background lives in `templates/sky_system.yaml`; `sky_system_tesla.yaml` is the Tesla-heavy variant.
- **The dashboard repo at `/root/HomeAssistant/` is the source of truth.** Edits go here first, then deploy via `scripts/install_wife_approved_mobile_forge.py` or the targeted scripts in `INSTALL/`. Never edit `/opt/ha-vps/homeassistant/dashboards/mobile_forge v5.yaml` directly without mirroring the change back into the repo.

## Workflow before making changes

1. Read this file and the relevant `.claude/memory/*.md`.
2. Query HA via the `ha-mcp` MCP server for current entity states / availability before assuming an entity exists.
3. Use Context7 for current docs on Lovelace, button-card, card-mod, Mushroom, Bubble Card, ApexCharts, Frigate/WebRTC.
4. Validate YAML.
5. Use Playwright to take before/after screenshots of dashboard changes when UI is involved.
6. Commit with a clear message after a working change.
7. Update the relevant `.claude/memory/*.md` if the fix taught us something durable (entity rename, card quirk, deploy gotcha).

## What NOT to write to memory

- Secrets (HA token, SSH keys, API keys, webhook URLs with auth).
- Ephemeral debugging state — that lives in commits, not memory.
- Anything already documented in this file or in the README.
