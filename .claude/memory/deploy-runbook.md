# Deploy runbook

The mental model: edit in `/root/HomeAssistant/` → validate → backup → deploy → reload (not restart unless required).

## 1. Validate YAML before anything

From the host:
```bash
docker exec homeassistant python -m homeassistant --script check_config -c /config
```
If that's slow, lint locally with `yamllint` first:
```bash
yamllint /root/HomeAssistant/views /root/HomeAssistant/templates
```

## 2. Backup

The convention in `/opt/ha-vps/homeassistant/` is `<filename>.<reason>-<YYYYMMDD-HHMMSS>`. Before overwriting `mobile_forge v5.yaml`:
```bash
TS=$(date +%Y%m%d-%H%M%S)
cp "/opt/ha-vps/homeassistant/dashboards/mobile_forge v5.yaml" \
   "/opt/ha-vps/homeassistant/dashboards/mobile_forge v5.yaml.before-<reason>-${TS}"
```

## 3. Deploy

Two paths exist in the repo:
- **Whole-dashboard rebuild:** `python3 scripts/install_wife_approved_mobile_forge.py --config-dir /opt/ha-vps/homeassistant`
- **Surgical updates** (preferred when you only changed one view):
  - `INSTALL/deploy.py`
  - `INSTALL/merge_into_mobile_forge.py`
  - `INSTALL/replace_home_view.py`

Read the script header before running — they target different layers (whole file vs. single view vs. merging templates).

## 4. Reload, not restart

| Change | Action |
|---|---|
| Lovelace YAML (views, templates, dashboard files) | Frontend refresh on the device. If resources changed: dev tools → "Reload Lovelace resources". |
| Theme files | "Reload themes" service or `homeassistant.reload_core_config`. |
| `configuration.yaml`, `automations.yaml`, `scripts.yaml` | "Reload config" via `homeassistant.reload_*` services or developer tools. |
| Custom integration code change | Restart container: `docker restart homeassistant`. |
| New HACS install / Python dependency | Restart container. |

For Lovelace YAML changes only, **do not restart**. Just reload the dashboard from the iOS app (pull-to-refresh works) or hit the Lovelace "Reload resources" button.

## 5. Commit

```bash
cd /root/HomeAssistant
git add -p           # review chunks
git commit -m "fix(views): <one-line what changed>"
git push             # only if remote is set up and you intend to publish
```

## 6. Post-deploy checks

- iOS Companion app: open Mobile Forge dashboard, verify the home view, swipe through tabs.
- Playwright (once installed): `npx playwright test` or run the `dashboard-smoke` spec to capture screenshots.
- Tail the log if anything looks off: `docker logs --tail 200 -f homeassistant`.

## Common deploy gotchas

- The deployed filename has a **literal space**: `mobile_forge v5.yaml`. Quote it everywhere.
- Lovelace `mode: storage` in `configuration.yaml` doesn't apply to the YAML-mode dashboards listed under `lovelace.dashboards.*` — those are file-driven and survive UI edits being overwritten by the YAML.
- Reload-resources doesn't pick up changes to template definitions inside a view file — you may need a full frontend cache-bust (Ctrl-Shift-R / clear iOS app cache).
