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

Also note: deployed dashboard's navbar links to `/mobile-forge/media`, but every view's `path` is `music`. The link is broken in every view's bottom nav. The repo `views/music.yaml` (2026-05-09) ships the corrected `/mobile-forge/music` route — sweep the other views' navbars when next touched.

---

## TVs can't be turned on (LG Bedroom + others)

**Symptom:** `media_player.turn_on` on `media_player.bed_room_tv` does nothing once the TV is fully off. `turn_off` works.

**Root cause:** The webostv config entry has only `host` + `client_secret`, no MAC. webOS over IP cannot wake a TV from full standby — the integration needs Wake-on-LAN. WOL packet must reach the TV's subnet (192.168.50.0/24), which is reachable via the `wg0` WireGuard tunnel from this VPS.

**Fix path:**
1. Get the LG TV's wired MAC from the TV menu: Settings → All Settings → General → About this TV.
2. Add the `wake_on_lan:` integration to `configuration.yaml`.
3. Create a script `script.bedroom_tv_wake` that calls `wake_on_lan.send_magic_packet` with `mac: <MAC>` and `broadcast_address: 192.168.50.255`.
4. In HA UI: Settings → Devices → LG webOS TV UA7700PUB → Configure → set "TV power on action" to call `script.bedroom_tv_wake`.
5. On the TV itself: enable Settings → General → Mobile TV On (LG calls this "Mobile TV on"/"Wake on LAN") and connect via Ethernet for reliability.
6. Verify the WireGuard tunnel forwards UDP/9 broadcast to 192.168.50.255 — if not, magic packet won't reach the TV; alternative is running a small WOL relay on a host inside the home LAN.

**Fire TV (`media_player.luna_s_firetvstick`) cannot turn_on at all via `alexa_media`.** To control power, either: (a) replace with the `androidtv` integration pointing at the Fire TV's IP (it's an Android device), or (b) use HDMI-CEC from the bedroom LG when both are on the same TV's HDMI chain.

**Kitchen TCL (`media_player.32q3k_2`) `androidtv_remote`** has host + MAC configured and supports turn_on/turn_off natively. If it still doesn't power on, confirm the TV has "Network standby"/"Wake on LAN over Wi-Fi" enabled in its system settings.

---

## Only YouTube media title shows on the TV tile

**Symptom:** Dashboard tile shows "Playing" when YouTube is on the LG, blank/state-only otherwise.

**Root cause:** Most webOS apps don't report `media_title` to the integration. They only report `app_id`/`app_name`. The previous `mf_tile` template only displayed `entity.state`, so no app/title surfaced.

**Fix:** Use `custom:mini-media-player` (already in `/hacsfiles/mini-media-player/` and registered in `lovelace_resources`) — it displays `app_name`, `media_title`, artwork, and renders native controls/source. See current `views/music.yaml` for the styled config (card_mod glass treatment to match the Mobile Forge look).

---

## Lights panel pointed at dead Govee entities (2026-05-15)

**Symptom:** "All living room", "Mike's side", "Kiara's side" tiles did nothing.

**Root cause:** Tiles hardcoded the Govee IDs (`light.living_room_2`,
`light.mike_side_lamp`, `light.kiara_side_lamp`) which are all `unavailable`
— the Govee integration/devices are offline. The real lights were the Hue
group `light.living_room` and two new Hue lamps that came in with the ugly
default IDs `light.hue_color_lamp_2/3` and were absent from the panel.

**Fix applied:** Renamed the two Hue lamps in the registry to
`light.kiara_lamp` / `light.mike_lamp`, rewired `views/lights.yaml` to the
live Hue entities, added `mf_light_tile` (tap=toggle, hold=more-info for full
Hue color/brightness). See `device-map.md` for the full mapping and the list
of automations/scripts/home-summary that **still** reference the dead Govee
IDs and need the same reconciliation.

**Registry rename procedure (durable):** entity_id edits in
`.storage/core.entity_registry` must be done with HA **stopped**
(`docker stop homeassistant` → edit JSON → `docker start`). Editing while
running gets clobbered when HA writes the registry on shutdown. Always back
up to `.before-<reason>-<TS>` first.

---

## `sed -i` footgun — emptied views/lights.yaml

**Symptom:** A `sed -i 's/.../.../' views/lights.yaml` left the file 0 bytes
(`md5 == d41d8cd9...` = empty file).

**Root cause:** The Bash tool resets cwd to `/root` between calls. A relative
path (`views/lights.yaml`) + an in-place stream edit went wrong and truncated
the file. Recovered with `git checkout -- views/lights.yaml`.

**Rule:** For edits to repo files use the Edit/Write tools, not `sed -i`.
If shell editing is unavoidable, use **absolute paths** and back up first.
The repo being under git is the only reason this was a non-event.
