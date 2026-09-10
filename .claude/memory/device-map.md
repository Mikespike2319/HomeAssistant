# Device map — lights (and integration ownership)

Created 2026-05-15 from live entity/device registry. CLAUDE.md referenced
this file but it didn't exist; this is the first cut, lights only.

## Light entities by integration

### Hue (behind the bridge — `via_device` set, full color/brightness)

| entity_id | device name | model | area | notes |
|---|---|---|---|---|
| `light.living_room` | Living room | Room (group) | Living Room | **Hue room group** — use this for "all living room" |
| `light.bedroom` | Bedroom | Room (group) | Bedroom | Hue room group — "all bedroom" |
| `light.couch` | Couch | lightstrip outdoor | Living Room | |
| `light.tv` | Tv | lightstrip outdoor | Living Room | |
| `light.backlight_tv` | Backlight Tv | Hue play gradient | Living Room | |
| `light.ceiling` | Ceiling | Hue color lamp | Living Room | often `unavailable` (switched off at wall) |
| `light.ceiling_2` | Ceiling 2 | Hue color lamp | Living Room | often `unavailable` |
| `light.kiara_lamp` | Kiara Lamp | Hue color lamp | Bedroom | **renamed 2026-05-15** from `light.hue_color_lamp_2` |
| `light.mike_lamp` | Mike Lamp | Hue color lamp | Bedroom | **renamed 2026-05-15** from `light.hue_color_lamp_3` |

The two `*_lamp` IDs were renamed in `.storage/core.entity_registry` (HA
stopped → edit → start). They're the real bedside lamps; they replaced the
dead Govee side lamps. unique_ids: kiara=`34eec9cb-302a-4f5a-8174-567e3f256c6b`,
mike=`78d329fb-81c0-4e6f-b72f-672cd051e962`.

### Nanoleaf

| `light.light_panels_51_66_88` | Light Panels 51:66:88 | NL22 | Bedroom | the actual "Light panels" |

### Govee — partial recovery as of 2026-06-01 (integration healthy, polling cloud)

Integration `custom_components.govee` (cloud API, `govee_api_laggat`) is loaded
and actively polling — confirmed via the recorder DB + live log. All 4 devices
and entities are still registered (none disabled). Status from a 2026-06-01
scan (recorder DB `home-assistant_v2.db`, read-only):

| entity_id | model | live state (2026-06-01) | was used as | replaced by |
|---|---|---|---|---|
| `light.big_lamp` | H6008 | **on / online** — BACK (was offline 05-15) | "Big lamp" tile | tile kept, now live |
| `light.living_room_2` | H615C | unavailable since 05-30 22:32 | "All living room" tile | `light.living_room` (Hue) |
| `light.mike_side_lamp` | H6008 | unavailable since 05-30 22:32 | "Mike's side" tile | `light.mike_lamp` (Hue) |
| `light.kiara_side_lamp` | H6008 | unavailable since 05-30 22:32 | "Kiara's side" tile | `light.kiara_lamp` (Hue) |

The 3 unavailable lamps all flipped at the same timestamp (05-30 22:32) — an
HA restart/integration reload after which only Big Lamp reconnected at the
Govee cloud. They're offline device-side, not an HA detection failure.

**colorTem bug + fix (2026-06-01):** Govee H6008 advertises `color_temp`
support but its `colorTem.range` is inverted (integration bug) — HA's native
more-info color-temp slider throws `API-Error 400 colorTem 6667`. Scenes/
scripts already dodge this with `hs_color`. The dashboard's `mf_light_tile`
opened native more-info on hold/double-tap, so Big Lamp's tile triggered it.
Fix: added `mf_govee_tile` template (`templates/mobile_forge_tiles.yaml`)
that extends `mf_light_tile` but sets `hold_action`/`double_tap_action` to
`none`; Big Lamp's tile (`views/lights.yaml`) now uses it. Tap still toggles;
adjust Govee brightness/color via scenes or the Govee app.

**Naming trap:** `light.living_room` (Hue group) and `light.living_room_2`
(dead Govee strip) both have friendly_name "Living room". Always check the
platform, not the friendly name.

## Still-stale references (NOT yet fixed — follow-up)

- The deployed `mobile_forge v5.yaml` **home view** still has a JS "all lights"
  summary array listing the dead Govee IDs (lines ~72/74) — not yet touched.

`automations.yaml`/`scripts.yaml`/`scenes.yaml` were reconciled to the Hue IDs
on 2026-07-07 (see media/Sonos fix entry below) — that part of this note is
now resolved.

## Govee cloud integration — rate limit (fixed 2026-07-07)

**Symptom:** ALL 4 Govee entities (including the live `light.big_lamp`) went
`unavailable` simultaneously at an HA restart, and `home-assistant.log.1` grew
to 1.2GB of Govee/Blink spam.

**Root cause:** The `govee` config entry's `delay` was `10` (seconds). With 4
devices polled that often, HA blew through Govee cloud's 10,000
requests/24h quota — `API-Error 429: rate limited!` — which kills the
**entire** config entry at setup (all 4 entities unavailable together,
identical `last_updated` timestamp — that's the tell that distinguishes this
from actual dead hardware, where entities go unavailable independently).

**Fix:** `.storage/core.config_entries` → `govee` entry → `data.delay` set to
`60`. Keeps daily request volume safely under quota. Do not drop it back
below ~30s with 4 devices. The 3 genuinely-dead lamps (`light.living_room_2`,
`light.mike_side_lamp`, `light.kiara_side_lamp`, offline device-side since
2026-05-30) are unaffected by this — they'll stay `unavailable` regardless of
delay; only `light.big_lamp` recovers once the rate limit window resets.

## Sonos / Cast / webOS media fix (2026-07-07)

**Sonos static hosts corrected** (`configuration.yaml` `sonos:` block) — the
previous single stale host `192.168.50.51` (mislabeled "Den") is gone;
correct live hosts:
- `192.168.50.44` = Sonos Era 100 "Media Room" → registers as
  `media_player.media_room`
- `192.168.50.52` = Sonos Era 100 "Den" → registers as `media_player.den`

Connecting to just these two also surfaced the rest of the Sonos household
(shared zone-group topology) as `media_player.kitchen` and
`media_player.roam_2`, even though they weren't in the static hosts list —
one reachable speaker is enough to learn about the whole household.

**Cast known_hosts** (`.storage/core.config_entries`, `cast` entry,
`data.known_hosts`) set to `["192.168.50.55", "192.168.50.6"]` (Living Room
Chromecast + LG webOS TV's built-in Cast receiver). New/recovered entities:
- `media_player.living_room_tv` (cast) — Living Room Chromecast, now `off`/available
- `media_player.lg_webos_tv_ua7700pub_2` (cast) — LG TV's Cast receiver, now `off`/available
- `media_player.bed_room_tv` (webostv, native) — recovered from `unavailable` to `off`

**Known residual issue:** `media_player.lg_webos_tv_ua7700pub` (the *original*
cast entity, no `_2` suffix) is still stuck `unavailable` — looks like a
stale duplicate device registration from before `known_hosts` was set (same
`config_entry_id`, different `unique_id`/`device_id` from the `_2` entity).
Needs manual cleanup in Settings → Devices (delete the stale device) — left
alone rather than edited directly in the registry since it's not certain
which one Michael's dashboards/automations may already reference.

**Area-label note:** `media_player.bed_room_tv`'s HA Area is "Bedroom", but
there is no Sonos in the Bedroom — every automation that pairs this TV with
audio/lighting (old `tv_entertainment_mode` and the new Movie
Mode/handoff automations added 2026-07-07) actually pairs it with the
**Living Room** lights and the **Media Room** Sonos, matching established
automation convention rather than the Area registry. If the TV's physical
room is actually the Media Room (not Bedroom), the Area assignment itself
should probably be corrected in HA.
