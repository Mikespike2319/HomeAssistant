# Common errors and recurring fixes

Append to this file when a fix teaches us something durable.

## Missing /local/ assets (cloud question marks, broken Tesla image)

**Symptom:** Animated clouds, background, trees, fence, lamp, or Tesla car images render as broken-image placeholders or question marks in the iOS Companion app and browser.

**Root cause:** `templates/sky_system.yaml` and `templates/sky_system_tesla.yaml` reference images under `/local/sky/`, `/local/backgrounds/`, `/local/bottom_overlays/New/{lamp,trees,fence}/`, and `/local/tesla/car/`. HA serves `/local/` from `/config/www/` — physically `/opt/ha-vps/homeassistant/www/` on this VPS. Those subdirectories don't exist. The 2026-05-05 automatic backup also doesn't contain them, so they've been 404ing since at least then.

**Why redeploys don't fix it:** The deploy scripts in `INSTALL/` and `scripts/` deploy YAML, not assets. Repo `assets/` (`model-y-juniper.png` is the only file there) isn't synced to `/opt/ha-vps/homeassistant/www/`.

**Permanent fix once asset source is known:**
1. Source assets — original creator's GitHub, user upload, or strip the dependency.
2. Place under `/root/HomeAssistant/assets/www/` mirroring the target tree.
3. Update or add a deploy step that rsyncs `repo/assets/www/` → `/opt/ha-vps/homeassistant/www/`.
4. Verify with `docker exec homeassistant ls /config/www/sky` and from the iOS app.

**Full list of expected paths:** see `templates/sky_system.yaml` `templates/sky_system_tesla.yaml` (run `grep -oE '/local/[A-Za-z0-9._/?-]+'` to enumerate).

---

## Mobile Forge home view replaced by stock view after a deploy

**Symptom:** Active home page is no longer the cozy/sky_system styled one — it shows generic HA cards.

**Root cause:** A previous session ran a "rebuild" deploy script that overwrote `mobile_forge v5.yaml` with stock content. The active home view should always start with `type: custom:button-card` + `template: sky_system`.

**Quick fix:** `python3 scripts/install_wife_approved_mobile_forge.py --config-dir /opt/ha-vps/homeassistant`, OR run `INSTALL/replace_home_view.py` to restore just the home view from the repo.

---

## iPhone viewport (recurring)

Add details when the next iPhone-viewport regression hits — what changed, how it was confirmed, what fixed it.

---

## Music tab regressing after deploy

Add details next time it happens — likely cause is `views/music.yaml` not being merged into the active dashboard during deploy.
