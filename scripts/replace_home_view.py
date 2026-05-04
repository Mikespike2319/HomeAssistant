#!/usr/bin/env python3
"""Replace the Mobile Forge Home view contents with the Wife Approved
animated-sky landing page.

Preserves: navbar-card (bottom nav).
Moves: old 10 cards to a new "Forge Classic" view so nothing is lost.
Replaces: Home view's main content with cozy sky-system tiles.
"""

import sys
import yaml
from pathlib import Path

DASH = Path("/opt/ha-vps/homeassistant/dashboards/mobile_forge v5.yaml")


def load(p):
    with open(p) as f:
        return yaml.safe_load(f)


def save(p, d):
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w") as f:
        yaml.dump(d, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=140)
    tmp.replace(p)


# ────────────────────────────────────────────────────────────
#  New Home view — Wife Approved animated sky landing
# ────────────────────────────────────────────────────────────
def build_new_home(navbar_card):
    """Compact tiles layered on top of the real sky_system backdrop."""
    cards = [
        # 1. Backdrop - animated sky, sun/moon arc, weather particles,
        #    greeting at top of viewport, El Rocco HUD at bottom.
        {"type": "custom:button-card", "template": "sky_system"},

        # 2. Cozy weather hero — current conditions + friendly summary
        {
            "type": "custom:button-card",
            "template": "cozy_weather_hero",
            "variables": {"weather_entity": "weather.forecast_home"},
        },

        # 3. El Rocco summary tile (compact) — 1 row of car status
        {
            "type": "custom:button-card",
            "show_name": False,
            "show_icon": False,
            "tap_action": {"action": "navigate", "navigation_path": "/mobile-forge/tesla"},
            "custom_fields": {
                "body": (
                    "[[[\n"
                    "  const get = (e) => states[e] ? states[e].state : null;\n"
                    "  const num = (e) => { const v = get(e); const n = parseFloat(v); return isNaN(n) ? null : n; };\n"
                    "  const soc = Math.round(num('sensor.el_rocco_battery_level') ?? 0);\n"
                    "  const range = Math.round(num('sensor.el_rocco_battery_range') ?? 0);\n"
                    "  const inside = Math.round(num('sensor.el_rocco_inside_temperature') ?? 0);\n"
                    "  const isLocked = get('lock.el_rocco_lock') === 'locked';\n"
                    "  const isCharging = get('binary_sensor.el_rocco_charge_cable') === 'on';\n"
                    "  const sentry = get('switch.el_rocco_sentry_mode') === 'on';\n"
                    "  let status;\n"
                    "  if (isCharging) status = 'Sipping electrons \\u26a1';\n"
                    "  else if (sentry) status = 'Keeping watch \\ud83d\\udc41';\n"
                    "  else if (isLocked) status = 'All buttoned up \\ud83d\\udd12';\n"
                    "  else status = 'Resting';\n"
                    "  const fillClass = isCharging ? 'charge' : (soc < 15 ? 'crit' : soc < 30 ? 'low' : '');\n"
                    "  const fill = isCharging ? 'linear-gradient(90deg, #ffe0b8, #ffba9c)' : (soc < 15 ? 'linear-gradient(90deg, #ff9a8a, #f06b5a)' : 'linear-gradient(90deg, #ffd6a8, #ff9e7a)');\n"
                    "  return `\n"
                    "    <div style=\"\n"
                    "      position:relative; width:100%; height:100%;\n"
                    "      padding:14px 18px;\n"
                    "      border-radius:18px;\n"
                    "      background: linear-gradient(160deg, rgba(255,210,165,0.10) 0%, rgba(28,22,30,0.6) 60%, rgba(15,12,20,0.78) 100%);\n"
                    "      border: 1px solid rgba(255,235,215,0.12);\n"
                    "      backdrop-filter: blur(14px) saturate(140%);\n"
                    "      box-shadow: 0 6px 20px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.06);\n"
                    "      font-family: 'Inter', sans-serif;\n"
                    "    \">\n"
                    "      <div style=\"display:flex; align-items:center; gap:10px; margin-bottom:8px;\">\n"
                    "        <span style=\"font-size:24px;\">\\ud83d\\ude97</span>\n"
                    "        <span style=\"font-size:13px; color:rgba(255,235,215,0.92);\">El Rocco</span>\n"
                    "      </div>\n"
                    "      <div style=\"display:flex; align-items:baseline; gap:14px;\">\n"
                    "        <div style=\"font-size:36px; font-weight:200; color:rgba(255,245,230,0.97); letter-spacing:-0.02em;\">${soc}<span style=\"font-size:18px; opacity:0.7;\">%</span></div>\n"
                    "        <div style=\"font-size:13px; color:rgba(255,235,215,0.65);\">${range} mi \\u00b7 ${inside}\\u00b0 inside</div>\n"
                    "      </div>\n"
                    "      <div style=\"position:relative; margin-top:8px; width:100%; height:6px; background:rgba(0,0,0,0.35); border-radius:3px; overflow:hidden;\">\n"
                    "        <div style=\"position:absolute; top:0; left:0; bottom:0; width:${soc}%; background:${fill}; border-radius:3px; transition:width 1s ease-out;\"></div>\n"
                    "      </div>\n"
                    "      <div style=\"margin-top:8px; font-family:'Caveat','Georgia',cursive; font-style:italic; font-size:16px; color:rgba(255,225,205,0.85);\">${status}</div>\n"
                    "    </div>\n"
                    "  `;\n"
                    "]]]"
                ),
            },
            "styles": {
                "card": [
                    {"background": "none"},
                    {"border": "none"},
                    {"padding": "0"},
                    {"width": "100%"},
                    {"height": "150px"},
                    {"cursor": "pointer"},
                ],
                "custom_fields": {"body": [{"width": "100%"}, {"height": "100%"}]},
            },
        },

        # 4. Quick mood scenes
        {
            "type": "horizontal-stack",
            "cards": [
                {"type": "custom:button-card", "template": "cozy_scene_pill",
                 "variables": {"scene_entity": "scene.living_room_dreamy_dusk", "label": "Cozy", "emoji": "🕯", "accent": "warm"}},
                {"type": "custom:button-card", "template": "cozy_scene_pill",
                 "variables": {"scene_entity": "scene.living_room_nighttime", "label": "Movie", "emoji": "🎬", "accent": "neutral"}},
                {"type": "custom:button-card", "template": "cozy_scene_pill",
                 "variables": {"scene_entity": "scene.living_room_energize", "label": "Bright", "emoji": "☀️", "accent": "cool"}},
                {"type": "custom:button-card", "template": "cozy_scene_pill",
                 "variables": {"scene_entity": "scene.bedroom_nighttime", "label": "Sleep", "emoji": "🌙", "accent": "rose"}},
            ],
        },

        # 5. Security panel
        {
            "type": "custom:button-card",
            "template": "cozy_alarm_panel",
            "variables": {"alarm_entity": "alarm_control_panel.nas_blink_home_security"},
        },

        # 6. Lights — 4 most-used as compact tiles in a 2-column grid
        {
            "type": "grid",
            "columns": 2,
            "square": False,
            "cards": [
                {"type": "custom:button-card", "template": "cozy_light_tile",
                 "variables": {"light_entity": "light.living_room_2", "cute_name": "Living room", "icon_emoji": "🛋"}},
                {"type": "custom:button-card", "template": "cozy_light_tile",
                 "variables": {"light_entity": "light.bedroom", "cute_name": "Bedroom", "icon_emoji": "🛏"}},
                {"type": "custom:button-card", "template": "cozy_light_tile",
                 "variables": {"light_entity": "light.couch", "cute_name": "Couch", "icon_emoji": "🛋"}},
                {"type": "custom:button-card", "template": "cozy_light_tile",
                 "variables": {"light_entity": "light.tv", "cute_name": "TV", "icon_emoji": "📺"}},
            ],
        },

        # 7. Quick actions row (lock car, all lights off, arm home)
        {
            "type": "horizontal-stack",
            "cards": [
                {"type": "custom:button-card", "template": "cozy_scene_pill",
                 "variables": {"label": "Lock El Rocco", "emoji": "🔒", "accent": "neutral"},
                 "tap_action": {"action": "call-service", "service": "lock.lock", "target": {"entity_id": "lock.el_rocco_lock"}}},
                {"type": "custom:button-card", "template": "cozy_scene_pill",
                 "variables": {"label": "All lights off", "emoji": "💤", "accent": "warm"},
                 "tap_action": {"action": "call-service", "service": "light.turn_off", "target": {"entity_id": "all"}}},
                {"type": "custom:button-card", "template": "cozy_scene_pill",
                 "variables": {"label": "Tuck us in", "emoji": "🛏", "accent": "rose"},
                 "tap_action": {"action": "call-service", "service": "alarm_control_panel.alarm_arm_home",
                                "target": {"entity_id": "alarm_control_panel.nas_blink_home_security"}}},
            ],
        },
    ]

    # Append navbar at end (preserved from old Home)
    if navbar_card:
        cards.append(navbar_card)
    return cards


def main():
    print(f"\n[1/6] Loading {DASH.name}...")
    d = load(DASH)
    home = next(v for v in d["views"] if v.get("path") == "home")
    old_cards = home["sections"][0].get("cards", [])
    n_old = len(old_cards)
    print(f"      ✓ Home view found, {n_old} cards currently")

    # Find the navbar to preserve
    navbar = next((c for c in old_cards if c.get("type") == "custom:navbar-card"), None)
    print(f"      ✓ navbar-card to preserve: {navbar is not None}")

    # Save old cards to a new "Forge Classic" view (minus the
    # backdrop card we previously added + navbar which we re-add)
    classic_cards = [c for c in old_cards
                     if not (c.get("type") == "custom:button-card"
                             and c.get("template") in ("sky_system", "sky_system_tesla"))
                     and c.get("type") != "custom:navbar-card"]

    print(f"\n[2/6] Preserving {len(classic_cards)} old Home cards in new 'Forge Classic' view")
    classic_view = {
        "title": "Forge Classic",
        "path": "forge-classic",
        "icon": "mdi:archive-outline",
        "type": "sections",
        "max_columns": 2,
        "sections": [{"type": "grid", "cards": classic_cards + ([navbar] if navbar else [])}],
    }
    # Ensure no duplicate forge-classic from previous run
    d["views"] = [v for v in d["views"] if v.get("path") != "forge-classic"]

    print(f"\n[3/6] Building new Home view (Wife Approved sky_system layout)...")
    new_home_cards = build_new_home(navbar)
    print(f"      ✓ {len(new_home_cards)} cards in new Home")

    # Replace the Home view's cards
    home["sections"] = [{"type": "grid", "cards": new_home_cards}]

    # Insert Forge Classic view at the end (before Settings if present)
    settings_view = next((v for v in d["views"] if v.get("path") == "settings"), None)
    if settings_view:
        d["views"].remove(settings_view)
        d["views"].append(classic_view)
        d["views"].append(settings_view)
    else:
        d["views"].append(classic_view)

    print(f"\n[4/6] Writing back to {DASH.name}...")
    save(DASH, d)
    print(f"      ✓ wrote {DASH} ({DASH.stat().st_size} bytes)")

    print(f"\n[5/6] Re-parse to validate YAML...")
    try:
        d2 = load(DASH)
        home2 = next(v for v in d2["views"] if v.get("path") == "home")
        n_new = len(home2["sections"][0]["cards"])
        has_sky = any(c.get("type") == "custom:button-card"
                      and c.get("template") == "sky_system"
                      for c in home2["sections"][0]["cards"])
        has_sky_template = "sky_system" in (d2.get("button_card_templates", {}) or {})
        paths = [v.get("path") for v in d2["views"]]
        print(f"      ✓ YAML valid")
        print(f"      ✓ Home cards: {n_old} → {n_new}")
        print(f"      ✓ template:sky_system in Home: {has_sky}")
        print(f"      ✓ button_card_templates has sky_system: {has_sky_template}")
        print(f"      ✓ paths unique: {len(paths) == len(set(paths))}")
        print(f"      ✓ paths: {paths}")
    except Exception as e:
        print(f"      ✗ FAILED: {e}")
        sys.exit(1)

    print(f"\n[6/6] DONE — restart HA next to pick up YAML changes\n")


if __name__ == "__main__":
    main()
