# Media integration review

## Confirmed dashboard entities

| Zone | Entity | Integration signal |
|---|---|---|
| Bedroom TV | `media_player.bed_room_tv` | Primary now-playing target |
| Living room TV | `media_player.lg_webos_tv_ua7700pub` | LG webOS |
| Kitchen TV | `media_player.32q3k_2` | TCL / Android TV Remote |
| Fire TV | `media_player.luna_s_firetvstick` | Fire TV route |
| Den | `media_player.den` | Sonos Era 100 |
| Portable | `media_player.roam_2` | Sonos Roam |
| Spotify | `media_player.spotify_michael_sanchez` | Spotify Connect |
| Echo Dot | `media_player.michael_s_2nd_echo_dot` | Alexa Media Player |

`media_player.lg_webos_tv_6651` also appears in the legacy Music view and
deployed snapshot, but it is not treated as a separate production zone until
its relationship to `media_player.bed_room_tv` is confirmed in the live entity
registry.

## Controls added to Signal room

- Live whole-home zone summary: playing, paused, and buffering entities.
- Previous, play/pause, and next controls for the primary Bedroom TV.
- Volume down, state-aware mute/unmute, and volume up.
- Kitchen TV and Sonos Roam, which were integrated but missing from the current
  Media view.
- One-tap **Pause everywhere** across all confirmed zones.
- Confirmed **Screens off** action for all four screen targets.

The actions use standard `media_player` services and do not require a new HACS
card or helper script.

## Deliberately not guessed

- TV or Fire TV app/source names for Netflix, YouTube, Plex, and similar
  shortcuts. `media_player.select_source` requires exact source strings from
  each entity's `source_list`.
- Sonos group membership and favorite IDs. Those need current live attributes
  before adding reliable group/join or favorite buttons.
- Power-on automation for the Bedroom LG. The repo documents that Wake-on-LAN
  is not configured yet, so a power-on button would be misleading.

Once live entity attributes are available, the next worthwhile layer is a
source launcher, Sonos room grouping, and a true Movie Night script that
combines lighting, TV source, volume, and security state.
