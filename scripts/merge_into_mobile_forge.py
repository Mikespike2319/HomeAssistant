#!/usr/bin/env python3
"""Merge Wife Approved templates + views INTO the existing Mobile Forge YAML.

Non-destructive: preserves all existing cards on existing views,
adds the Wife Approved sky_system backdrop on every view, appends
cozy widget rows to Lights/Tesla/Security, and adds 3 new views
(Music, House, Weather).
"""

from __future__ import annotations

import sys
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DASH_PATH = Path("/opt/ha-vps/homeassistant/dashboards/mobile_forge v5.yaml")
COZY = REPO_ROOT


def load_yaml(p: Path) -> dict:
    with open(p) as f:
        return yaml.safe_load(f)


# ─────────────────────────────────────────────────────────────────
#  Build button_card_templates dict from all template files
# ─────────────────────────────────────────────────────────────────
def collect_templates() -> dict:
    files = sorted((COZY / "templates").glob("*.yaml"))
    templates = {}
    for f in files:
        d = load_yaml(f)
        templates.update(d.get("button_card_templates", {}))
    return templates


# ─────────────────────────────────────────────────────────────────
#  Cozy backdrop card — added to every view as first card
# ─────────────────────────────────────────────────────────────────
def backdrop_card() -> dict:
    return {
        "type": "custom:button-card",
        "template": "sky_system",
    }


# ─────────────────────────────────────────────────────────────────
#  Convert one of my view files (cards: top-level) into a list of
#  cards suitable for appending to an existing view's first section.
#  Skips the backdrop card (already added separately) and the
#  page-header markdown (existing view has its own header).
# ─────────────────────────────────────────────────────────────────
def view_cards(filename: str, skip_first_n: int = 2) -> list:
    """Load a cozy view yaml, return its cards array, optionally
    skipping the first N (backdrop + header)."""
    v = load_yaml(COZY / "views" / filename)
    cards = v.get("cards", [])
    return cards[skip_first_n:]


# ─────────────────────────────────────────────────────────────────
#  Build full new views (Music, House, Weather) — keep navbar-card
#  shared with existing views by passing it in.
# ─────────────────────────────────────────────────────────────────
def navbar_card_from(d: dict) -> dict | None:
    """Find the navbar-card from any existing view to reuse on new views."""
    for v in d.get("views", []):
        for s in v.get("sections", []):
            for c in s.get("cards", []):
                if c.get("type") == "custom:navbar-card":
                    return normalize_navbar(c)
    return None


def normalize_navbar(card: dict | None) -> dict | None:
    if not isinstance(card, dict):
        return None
    nav = dict(card)
    nav["type"] = "custom:navbar-card"
    nav["routes"] = [
        {"url": "/mobile-forge/home", "icon": "mdi:home"},
        {"url": "/mobile-forge/lights", "icon": "mdi:lightbulb-group"},
        {"url": "/mobile-forge/music", "icon": "mdi:music"},
        {"url": "/mobile-forge/tesla", "icon": "mdi:car-electric"},
        {"url": "/mobile-forge/security", "icon": "mdi:shield-lock"},
        {"url": "/mobile-forge/house", "icon": "mdi:home-thermometer"},
    ]
    nav["card_mod"] = {
        "style": (
            ":host { position: fixed !important; left: 12px !important; right: 12px !important; "
            "bottom: max(12px, env(safe-area-inset-bottom, 0px)) !important; z-index: 999 !important; }\n"
            "ha-card { border-radius: 22px !important; border: 1px solid rgba(255,255,255,0.12) !important; "
            "background: rgba(15,15,18,0.90) !important; backdrop-filter: blur(20px); "
            "-webkit-backdrop-filter: blur(20px); box-shadow: 0 18px 48px rgba(0,0,0,0.32) !important; "
            "padding-bottom: env(safe-area-inset-bottom, 0px); overflow: hidden; }\n"
        )
    }
    return nav


def nav_spacer_card() -> dict:
    return {"type": "custom:button-card", "template": "mf_nav_spacer"}


def ensure_bottom_chrome(cards: list, navbar_card: dict | None) -> None:
    cards[:] = [
        c for c in cards
        if not (
            isinstance(c, dict)
            and (
                c.get("type") == "custom:navbar-card"
                or (c.get("type") == "custom:button-card" and c.get("template") == "mf_nav_spacer")
            )
        )
    ]
    if navbar_card:
        cards.append(nav_spacer_card())
        cards.append(normalize_navbar(navbar_card))


def build_view(title, path, icon, cozy_view_filename, navbar_card) -> dict:
    """Build a full Mobile-Forge-style view (with sections wrapper)."""
    cozy_cards = load_yaml(COZY / "views" / cozy_view_filename).get("cards", [])
    section_cards = list(cozy_cards)
    ensure_bottom_chrome(section_cards, navbar_card)
    return {
        "title": title,
        "path": path,
        "icon": icon,
        "type": "sections",
        "max_columns": 2,
        "sections": [{"type": "grid", "cards": section_cards}],
    }


# ─────────────────────────────────────────────────────────────────
#  MAIN MERGE
# ─────────────────────────────────────────────────────────────────
def main():
    print(f"\n[1/5] Loading existing Mobile Forge ({DASH_PATH.name})...")
    d = load_yaml(DASH_PATH)
    n_views_before = len(d.get("views", []))
    print(f"      ✓ {n_views_before} existing views loaded")

    print(f"\n[2/5] Collecting dashboard templates from {COZY}...")
    templates = collect_templates()
    d["button_card_templates"] = templates
    print(f"      ✓ {len(templates)} templates added at root")

    navbar = navbar_card_from(d)
    if navbar:
        print(f"      ✓ found shared navbar-card to reuse on new views")

    print(f"\n[3/5] Walking existing views — adding backdrop + cozy widgets...")
    bd = backdrop_card()
    for v in d["views"]:
        path = v.get("path", "")
        title_old = v.get("title", "")
        sections = v.get("sections", [])
        if not sections:
            v["sections"] = sections = [{"type": "grid", "cards": []}]
        # Make sure the first section has cards array
        if "cards" not in sections[0]:
            sections[0]["cards"] = []
        cards = sections[0]["cards"]

        # Prepend backdrop on every view (idempotent — only if not already there)
        already_has_backdrop = any(
            c.get("type") == "custom:button-card" and c.get("template") in ("sky_system", "sky_system_tesla")
            for c in cards
        )
        if not already_has_backdrop:
            cards.insert(0, bd)

        # Per-view extra cozy content
        if path == "lights":
            extra = view_cards("lights.yaml", skip_first_n=2)
            cards.extend(extra)
            print(f"      ✓ Lights: appended {len(extra)} cozy cards")
        elif path == "tesla":
            v["title"] = "El Rocco"  # rename to match the car
            v["icon"] = "mdi:car-electric"
            extra = view_cards("tesla.yaml", skip_first_n=2)
            cards.extend(extra)
            print(f"      ✓ Tesla → El Rocco: appended {len(extra)} cozy cards")
        elif path == "security":
            extra = view_cards("security.yaml", skip_first_n=2)
            cards.extend(extra)
            print(f"      ✓ Security: appended {len(extra)} cozy cards")
        else:
            print(f"      • {title_old}: backdrop only (preserved {len(cards)-1} existing cards)")

        ensure_bottom_chrome(cards, navbar)

    print(f"\n[4/5] Adding 3 new views (Music, House, Weather)...")
    existing_paths = {v.get("path") for v in d["views"]}

    new_views = []
    if "music" not in existing_paths:
        new_views.append(build_view("Music", "music", "mdi:music",
                                     "music.yaml", navbar))
    if "house" not in existing_paths:
        new_views.append(build_view("House", "house", "mdi:home-thermometer",
                                     "house.yaml", navbar))
    if "weather" not in existing_paths:
        new_views.append(build_view("Weather", "weather", "mdi:weather-partly-cloudy",
                                     "weather.yaml", navbar))

    # Insert new views BEFORE Settings (so Settings stays last)
    if new_views:
        settings_view = next((v for v in d["views"] if v.get("path") == "settings"), None)
        if settings_view:
            d["views"].remove(settings_view)
        d["views"].extend(new_views)
        if settings_view:
            d["views"].append(settings_view)

    for nv in new_views:
        print(f"      ✓ added view: {nv['title']} (path={nv['path']})")

    n_views_after = len(d["views"])
    print(f"      → views: {n_views_before} → {n_views_after}")

    print(f"\n[5/5] Writing back to {DASH_PATH.name}...")
    tmp = DASH_PATH.with_suffix(DASH_PATH.suffix + ".tmp")
    with open(tmp, "w") as f:
        # Preserve YAML quirks; default_flow_style=False keeps it readable
        yaml.dump(d, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=120)
    tmp.replace(DASH_PATH)
    print(f"      ✓ wrote {DASH_PATH}")
    print(f"      ✓ size: {DASH_PATH.stat().st_size} bytes")

    # Final validation: parse what we just wrote
    print(f"\n[validate] Re-reading + parsing output...")
    try:
        with open(DASH_PATH) as f:
            d2 = yaml.safe_load(f)
        assert d2.get("title") == d.get("title")
        assert len(d2["views"]) == n_views_after
        assert "button_card_templates" in d2
        print(f"      ✓ VALID — {len(d2['views'])} views, {len(d2['button_card_templates'])} templates")
    except Exception as e:
        print(f"      ✗ FAILED parse: {e}")
        sys.exit(1)

    print(f"\n{'='*60}\n  ✓ MERGE COMPLETE\n{'='*60}\n")


if __name__ == "__main__":
    main()
