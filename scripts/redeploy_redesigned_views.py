#!/usr/bin/env python3
"""Redeploy the redesigned modular views INTO the live Mobile Forge dashboard.

REPLACE (not append) — unlike merge_into_mobile_forge.py, this swaps each
redesigned view wholesale so re-running is idempotent (no card duplication).

What it does:
  - button_card_templates <- the full repo template set (superset of live;
    includes sky_system, mf_nav_spacer, mf_govee_tile, etc.)
  - Replaces views: lights, media, music, house, tesla, security with their
    modular redesigned definitions from repo views/*.yaml.
  - Re-injects the navbar + nav_spacer chrome (modular views omit it) using the
    canonical navbar already present in the live dashboard.
  - Preserves the live view's wallpaper card_mod when the modular view lacks it.
  - Leaves home, sebastian, forge-classic, settings, weather untouched.

Writes atomically (temp -> rename) and validates the result before swapping.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DASH_PATH = Path("/opt/ha-vps/homeassistant/dashboards/mobile_forge v5.yaml")

# live view path -> modular source filename
REDESIGNED = {
    "lights": "lights.yaml",
    "media": "media.yaml",
    "music": "music.yaml",
    "house": "house.yaml",
    "tesla": "tesla.yaml",
    "security": "security.yaml",
}

NAVBAR_ROUTES = [
    {"url": "/mobile-forge/home", "icon": "mdi:home"},
    {"url": "/mobile-forge/lights", "icon": "mdi:lightbulb-group"},
    {"url": "/mobile-forge/media", "icon": "mdi:television-play"},
    {"url": "/mobile-forge/tesla", "icon": "mdi:car-electric"},
    {"url": "/mobile-forge/security", "icon": "mdi:shield-lock"},
    {"url": "/mobile-forge/house", "icon": "mdi:home-thermometer"},
]


def load_yaml(p: Path) -> dict:
    with open(p) as f:
        return yaml.safe_load(f)


def collect_templates() -> dict:
    templates: dict = {}
    for f in sorted((REPO_ROOT / "templates").glob("*.yaml")):
        d = load_yaml(f) or {}
        for name, tpl in (d.get("button_card_templates") or {}).items():
            templates[name] = tpl
    return templates


def normalize_navbar(card: dict | None) -> dict | None:
    if not isinstance(card, dict):
        return None
    nav = dict(card)
    nav["type"] = "custom:navbar-card"
    nav["routes"] = [dict(r) for r in NAVBAR_ROUTES]
    return nav


def find_navbar(d: dict) -> dict | None:
    for v in d.get("views", []):
        for s in v.get("sections", []):
            for c in s.get("cards", []):
                if isinstance(c, dict) and c.get("type") == "custom:navbar-card":
                    return normalize_navbar(c)
    return None


def is_chrome(c: dict) -> bool:
    return isinstance(c, dict) and (
        c.get("type") == "custom:navbar-card"
        or (c.get("type") == "custom:button-card" and c.get("template") == "mf_nav_spacer")
    )


def ensure_bottom_chrome(cards: list, navbar: dict | None) -> None:
    """Strip any existing navbar/spacer, then append spacer + navbar once."""
    cards[:] = [c for c in cards if not is_chrome(c)]
    if navbar:
        cards.append({"type": "custom:button-card", "template": "mf_nav_spacer"})
        cards.append(normalize_navbar(navbar))


def view_cards_count(v: dict) -> int:
    return sum(len(s.get("cards", [])) for s in v.get("sections", []))


def main() -> None:
    if not DASH_PATH.exists():
        sys.exit(f"FATAL: live dashboard not found: {DASH_PATH}")

    print(f"[1/4] Loading live dashboard ({DASH_PATH.name})...")
    d = load_yaml(DASH_PATH)
    n_views = len(d.get("views", []))
    print(f"      {n_views} views, {len(d.get('button_card_templates', {}))} templates")

    print("[2/4] Setting templates from repo + replacing redesigned views...")
    d["button_card_templates"] = collect_templates()
    navbar = find_navbar(d)
    if not navbar:
        sys.exit("FATAL: no navbar-card found in live dashboard to reuse")

    replaced = []
    for i, v in enumerate(d["views"]):
        path = v.get("path")
        if path not in REDESIGNED:
            continue
        nv = load_yaml(REPO_ROOT / "views" / REDESIGNED[path])
        if nv.get("path") != path:
            sys.exit(f"FATAL: modular {REDESIGNED[path]} path={nv.get('path')} != {path}")
        # preserve wallpaper card_mod from the live view if the modular lacks it
        if "card_mod" in v and "card_mod" not in nv:
            nv["card_mod"] = v["card_mod"]
        secs = nv.get("sections") or []
        if not secs:
            sys.exit(f"FATAL: modular {REDESIGNED[path]} has no sections")
        secs[-1].setdefault("cards", [])
        ensure_bottom_chrome(secs[-1]["cards"], navbar)
        d["views"][i] = nv
        replaced.append((path, view_cards_count(nv)))

    for path, n in replaced:
        print(f"      replaced '{path}' ({n} cards, navbar+spacer ensured)")
    if len(replaced) != len(REDESIGNED):
        sys.exit(f"FATAL: replaced {len(replaced)} of {len(REDESIGNED)} expected views")

    print("[3/4] Writing atomically + validating...")
    tmp = DASH_PATH.with_suffix(DASH_PATH.suffix + ".tmp")
    with open(tmp, "w") as f:
        yaml.dump(d, f, default_flow_style=False, sort_keys=False, allow_unicode=True, width=4096)

    d2 = yaml.safe_load(open(tmp))
    errors = []
    if len(d2.get("views", [])) != n_views:
        errors.append(f"view count {len(d2['views'])} != {n_views}")
    bct = d2.get("button_card_templates", {})
    for req in ("sky_system", "mf_nav_spacer", "mf_govee_tile", "mf_light_tile"):
        if req not in bct:
            errors.append(f"missing template {req}")
    for v in d2["views"]:
        if v.get("path") not in REDESIGNED:
            continue
        cards = [c for s in v.get("sections", []) for c in s.get("cards", [])]
        navs = sum(1 for c in cards if isinstance(c, dict) and c.get("type") == "custom:navbar-card")
        spcr = sum(1 for c in cards if isinstance(c, dict) and c.get("template") == "mf_nav_spacer")
        skys = sum(1 for c in cards if isinstance(c, dict) and c.get("template") in ("sky_system", "sky_system_tesla"))
        if navs != 1 or spcr != 1 or skys < 1:
            errors.append(f"{v['path']}: navbar={navs} spacer={spcr} sky={skys}")
    if errors:
        tmp.unlink(missing_ok=True)
        sys.exit("VALIDATION FAILED:\n  - " + "\n  - ".join(errors))

    print("[4/4] Swapping into place...")
    tmp.replace(DASH_PATH)
    print(f"      wrote {DASH_PATH} ({DASH_PATH.stat().st_size} bytes)")
    print(f"      views={len(d2['views'])} templates={len(bct)} replaced={[p for p,_ in replaced]}")
    print("\n  DONE — reload Lovelace on the device (yaml-mode re-reads on refresh).")


if __name__ == "__main__":
    main()
