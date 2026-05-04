#!/usr/bin/env python3
"""Deploy the standalone Cozy dashboard to a running HA instance.

Creates a new dashboard `cozy_home` (URL path: /cozy-home) with all
repo templates + 6 views. Non-destructive — does
not touch existing dashboards.
"""

import json
import sys
import time
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
HA_ROOT = Path("/opt/ha-vps/homeassistant")
STORAGE = HA_ROOT / ".storage"
COZY = REPO_ROOT

DASHBOARD_ID = "cozy_home"
URL_PATH = "cozy-home"
TITLE = "Cozy"
ICON = "mdi:home-heart"


def load_yaml(p: Path) -> dict:
    with open(p) as f:
        return yaml.safe_load(f)


def atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON atomically — temp file then rename."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)
    print(f"  ✓ wrote {path}")


def build_dashboard_config() -> dict:
    """Build the Lovelace dashboard config dict from our YAML files."""

    # Load templates from the repo.
    print("→ Loading templates...")
    template_files = sorted((COZY / "templates").glob("*.yaml"))
    button_card_templates: dict = {}
    for f in template_files:
        d = load_yaml(f)
        bct = d.get("button_card_templates", {})
        for name, tpl in bct.items():
            if name in button_card_templates:
                print(f"  ! duplicate template: {name}")
            button_card_templates[name] = tpl
            print(f"  • {name}")

    # Load all 6 views
    print("→ Loading views...")
    view_files = [
        COZY / "views" / "lights.yaml",
        COZY / "views" / "security.yaml",
        COZY / "views" / "music.yaml",
        COZY / "views" / "house.yaml",
        COZY / "views" / "weather.yaml",
        COZY / "views" / "tesla.yaml",
    ]
    views = []
    for f in view_files:
        v = load_yaml(f)
        views.append(v)
        print(f"  • {v.get('title','?')} (path={v.get('path','?')})")

    # Build the dashboard config
    cfg = {
        "title": TITLE,
        "views": views,
        "button_card_templates": button_card_templates,
    }
    return cfg


def write_dashboard_storage(cfg: dict) -> None:
    """Write .storage/lovelace.cozy_home with the dashboard config."""
    storage_file = STORAGE / f"lovelace.{DASHBOARD_ID}"
    payload = {
        "version": 1,
        "minor_version": 1,
        "key": f"lovelace.{DASHBOARD_ID}",
        "data": {"config": cfg},
    }
    atomic_write_json(storage_file, payload)


def register_dashboard_in_list() -> None:
    """Add a new entry to .storage/lovelace_dashboards."""
    f = STORAGE / "lovelace_dashboards"
    with open(f) as fh:
        d = json.load(fh)
    items = d["data"]["items"]

    # Already there? Skip
    for it in items:
        if it.get("id") == DASHBOARD_ID:
            print(f"  ✓ {DASHBOARD_ID} already registered, skipping")
            return

    new_id = max((it.get("id_prefix", 0) for it in items), default=0)
    new_entry = {
        "icon": ICON,
        "id": DASHBOARD_ID,
        "mode": "storage",
        "require_admin": False,
        "show_in_sidebar": True,
        "title": TITLE,
        "url_path": URL_PATH,
    }
    items.append(new_entry)
    atomic_write_json(f, d)
    print(f"  ✓ registered {URL_PATH} in sidebar")


def add_font_resource() -> None:
    """Add the Caveat/Dancing Script Google Font as a CSS resource."""
    f = STORAGE / "lovelace_resources"
    with open(f) as fh:
        d = json.load(fh)
    items = d["data"]["items"]

    font_url = (
        "https://fonts.googleapis.com/css2?"
        "family=Caveat:wght@400;500&"
        "family=Dancing+Script:wght@400;500&"
        "display=swap"
    )

    for it in items:
        if it.get("url") == font_url:
            print(f"  ✓ font resource already present, skipping")
            return

    # Generate a new id
    existing_ids = {it.get("id") for it in items}
    import secrets
    new_id = secrets.token_hex(16)
    while new_id in existing_ids:
        new_id = secrets.token_hex(16)

    items.append({
        "type": "css",
        "url": font_url,
        "id": new_id,
    })
    atomic_write_json(f, d)
    print(f"  ✓ Caveat font CSS registered as resource")


def copy_dashboard_assets() -> None:
    """Copy assets so Lovelace can serve them from /local/mobile-forge/."""
    src_dir = COZY / "assets"
    dst_dir = HA_ROOT / "www" / "mobile-forge"
    if not src_dir.exists():
        print("  • no assets directory found, skipping")
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted(src_dir.iterdir()):
        if src.is_file():
            dst = dst_dir / src.name
            import shutil
            shutil.copy2(src, dst)
            print(f"  ✓ copied {dst}")


def main():
    print(f"\n{'='*60}\n  COZY DASHBOARD DEPLOY\n{'='*60}\n")
    if not HA_ROOT.exists():
        print(f"FATAL: {HA_ROOT} not found — is HA installed here?")
        sys.exit(1)
    if not COZY.exists():
        print(f"FATAL: {COZY} not found — run from a system with the cozy build")
        sys.exit(1)

    print("[1/5] Building dashboard config from YAML sources...")
    cfg = build_dashboard_config()
    n_templates = len(cfg["button_card_templates"])
    n_views = len(cfg["views"])
    print(f"\n  → {n_templates} templates, {n_views} views ready")

    print("\n[2/5] Writing dashboard storage file...")
    write_dashboard_storage(cfg)

    print("\n[3/5] Registering dashboard in sidebar...")
    register_dashboard_in_list()

    print("\n[4/5] Adding Caveat font resource...")
    add_font_resource()

    print("\n[5/5] Copying local dashboard assets...")
    copy_dashboard_assets()

    print(f"\n{'='*60}")
    print(f"  ✓ DEPLOY COMPLETE")
    print(f"{'='*60}")
    print(f"\n  Dashboard URL: /{URL_PATH}")
    print(f"  Sidebar entry: '{TITLE}' (icon: {ICON})")
    print(f"\n  Next: reload Lovelace (hard-refresh browser, or restart HA)")
    print()


if __name__ == "__main__":
    main()
