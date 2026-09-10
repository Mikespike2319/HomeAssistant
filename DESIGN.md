# HearthOS design review

## Direction

HearthOS keeps the warm, calm personality of Mobile Forge while giving it a
more distinctive command-deck feel. The visual system is built around deep
midnight surfaces, cyan and violet aurora light, restrained amber accents, and
high-contrast typography that remains readable on an iPhone.

The production design uses only capabilities already present in this repo:
`custom:button-card`, `card-mod`, `navbar-card`, and native Home Assistant
cards. No new HACS dependency is required.

## Review findings addressed

- The primary animated background referenced `/local/` image trees that were
  missing on the Home Assistant host. `sky_system` is now asset-free CSS and
  reacts to day/night and storm state.
- The polished HTML preview and deployable Lovelace sources had drifted apart.
  Shared HearthOS titles, status language, glass materials, accents, and
  navigation styling now match.
- The one-shot installer synced only Home and Media. It now synchronizes every
  production view: Lights, Media, Tesla, Security, House, and Weather.
- The Weather view still used the older visual language and a generic external
  radar embed. It now uses native forecast cards plus compact sky telemetry.
- A House tile and the targeted replacement script still referenced the dead
  `light.living_room_2` Govee entity. Both now use the live Hue group
  `light.living_room`.
- The legacy Music view linked to broken or retired navigation routes. Its dock
  now points at the six production destinations.

## Interaction rules

- Primary tiles have at least 44 px touch targets and active states gain a
  subtle cyan/violet glow.
- Home weather is a drill-down to `/mobile-forge/weather`.
- Light tiles keep tap-to-toggle and hold-for-more-info behavior. The Big Lamp
  retains its Govee-specific protection against the broken color-temperature
  control.
- Motion is ambient only and disables itself when the client requests reduced
  motion.
- The bottom dock reserves safe-area padding for the iOS Companion app.

## Safe rollout

Run the installer in dry-run mode first:

```bash
python3 scripts/install_wife_approved_mobile_forge.py \
  --config-dir /opt/ha-vps/homeassistant \
  --dry-run
```

Then install, validate the Home Assistant configuration, and refresh Lovelace:

```bash
python3 scripts/install_wife_approved_mobile_forge.py \
  --config-dir /opt/ha-vps/homeassistant
docker exec homeassistant python -m homeassistant --script check_config -c /config
```

The installer creates a timestamped backup before writing. Lovelace-only
changes do not require a Home Assistant container restart.
