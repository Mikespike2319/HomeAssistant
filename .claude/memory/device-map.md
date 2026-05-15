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

### Govee — ALL UNAVAILABLE as of 2026-05-15 (integration/devices offline)

| entity_id | was used as | replaced by |
|---|---|---|
| `light.living_room_2` | "All living room" tile | `light.living_room` (Hue) |
| `light.mike_side_lamp` | "Mike's side" tile | `light.mike_lamp` (Hue) |
| `light.kiara_side_lamp` | "Kiara's side" tile | `light.kiara_lamp` (Hue) |
| `light.big_lamp` | "Big lamp" tile | none — tile kept, shows "offline" until Govee returns |

**Naming trap:** `light.living_room` (Hue group) and `light.living_room_2`
(dead Govee strip) both have friendly_name "Living room". Always check the
platform, not the friendly name.

## Still-stale references (NOT yet fixed — follow-up)

The dead Govee IDs are still wired into many scenes/automations:
- `automations.yaml` and `scripts.yaml` reference `light.living_room_2`,
  `light.mike_side_lamp`, `light.kiara_side_lamp` (entertainment/arrival/
  departure routines, scenes). Those service calls now hit dead entities.
- The deployed `mobile_forge v5.yaml` **home view** has a JS "all lights"
  summary array still listing the dead Govee IDs (lines ~72/74).
Only the Lights *panel view* + the `mf_light_tile` template were fixed on
2026-05-15. Reconcile automations/scripts/home-summary to the Hue IDs next.
