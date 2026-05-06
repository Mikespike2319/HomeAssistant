#!/usr/bin/env python3
"""
Install the Wife Approved animated sky system into the active Mobile Forge
Home Assistant dashboard.

This intentionally discovers the active /mobile-forge source before editing.
It backs up the active dashboard, installs button_card_templates.sky_system
from the Reddit-linked Pastebin, replaces the real Home view, and moves the
previous Home cards into a Forge Classic view.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import tempfile
import time
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "PyYAML is required. On Home Assistant OS/container it is usually present; "
        "otherwise run: python3 -m pip install pyyaml"
    ) from exc


PASTEBIN_RAW = "https://pastebin.com/raw/ZtzsKzHD"
TARGET_DASHBOARD_PATH = "mobile-forge"
TARGET_VIEW_PATH = "home"
CLASSIC_VIEW_PATH = "forge-classic"
REPO_ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def dump_yaml(path: Path, data: Any) -> None:
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with tmp.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(
                data,
                handle,
                sort_keys=False,
                allow_unicode=True,
                width=4096,
                default_flow_style=False,
            )
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, data: Any) -> None:
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def normalize_path(value: str | None) -> str:
    return (value or "").strip().strip("/")


def find_storage_item(config_dir: Path) -> dict[str, Any] | None:
    registry = config_dir / ".storage" / "lovelace_dashboards"
    if not registry.exists():
        return None
    raw = load_json(registry)
    items = raw.get("data", {}).get("items", [])
    for item in items:
        ids = {
            normalize_path(item.get("url_path")),
            normalize_path(item.get("path")),
            normalize_path(item.get("id")),
        }
        if TARGET_DASHBOARD_PATH in ids or TARGET_DASHBOARD_PATH.replace("-", "_") in ids:
            return item
    return None


def discover_active_source(config_dir: Path) -> dict[str, Any]:
    configuration = config_dir / "configuration.yaml"
    source: dict[str, Any] = {
        "dashboard_path": TARGET_DASHBOARD_PATH,
        "mode": None,
        "file": None,
        "storage_file": None,
        "storage_item": find_storage_item(config_dir),
        "from": None,
    }

    if configuration.exists():
        cfg = load_yaml(configuration)
        dashboards = ((cfg.get("lovelace") or {}).get("dashboards") or {})
        entry = dashboards.get(TARGET_DASHBOARD_PATH)
        if entry:
            mode = entry.get("mode", "yaml")
            source["mode"] = mode
            source["from"] = str(configuration)
            if mode == "yaml":
                filename = entry.get("filename")
                if not filename:
                    raise SystemExit("configuration.yaml defines mobile-forge in YAML mode but has no filename.")
                dash_file = Path(filename)
                if not dash_file.is_absolute():
                    dash_file = config_dir / dash_file
                source["file"] = dash_file
                return source

    item = source["storage_item"]
    if item:
        mode = item.get("mode", "storage")
        source["mode"] = mode
        source["from"] = str(config_dir / ".storage" / "lovelace_dashboards")
        if mode == "yaml":
            filename = item.get("filename")
            if not filename:
                raise SystemExit("lovelace_dashboards defines mobile-forge in YAML mode but has no filename.")
            dash_file = Path(filename)
            if not dash_file.is_absolute():
                dash_file = config_dir / dash_file
            source["file"] = dash_file
            return source

        storage_id = item.get("id") or TARGET_DASHBOARD_PATH.replace("-", "_")
        candidates = [
            config_dir / ".storage" / f"lovelace.{storage_id}",
            config_dir / ".storage" / f"lovelace.{TARGET_DASHBOARD_PATH}",
            config_dir / ".storage" / f"lovelace.{TARGET_DASHBOARD_PATH.replace('-', '_')}",
        ]
        for candidate in candidates:
            if candidate.exists():
                source["storage_file"] = candidate
                return source
        raise SystemExit(
            "Mobile Forge appears to be storage mode, but I could not find its .storage/lovelace.* file. "
            f"Checked: {', '.join(str(c) for c in candidates)}"
        )

    raise SystemExit(
        "Could not prove the active /mobile-forge dashboard source from configuration.yaml "
        "or .storage/lovelace_dashboards. Refusing to edit."
    )


def load_dashboard(source: dict[str, Any]) -> tuple[Any, Any]:
    if source["mode"] == "yaml":
        path = Path(source["file"])
        if not path.exists():
            raise SystemExit(f"Active dashboard file does not exist: {path}")
        return load_yaml(path), None

    storage_file = Path(source["storage_file"])
    wrapper = load_json(storage_file)
    config = wrapper.get("data", {}).get("config")
    if not isinstance(config, dict):
        raise SystemExit(f"Storage dashboard has no data.config object: {storage_file}")
    return config, wrapper


def save_dashboard(source: dict[str, Any], dashboard: Any, wrapper: Any | None) -> None:
    if source["mode"] == "yaml":
        dump_yaml(Path(source["file"]), dashboard)
        return
    assert wrapper is not None
    wrapper["data"]["config"] = dashboard
    dump_json(Path(source["storage_file"]), wrapper)


def backup_source(source: dict[str, Any]) -> Path:
    if source["mode"] == "yaml":
        src = Path(source["file"])
    else:
        src = Path(source["storage_file"])
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = src.with_name(f"{src.name}.wife-approved-backup-{stamp}")
    shutil.copy2(src, backup)
    return backup


def copy_dashboard_assets(config_dir: Path) -> list[Path]:
    """Copy repo assets into Home Assistant's /local served directory."""
    source_dir = REPO_ROOT / "assets"
    target_dir = config_dir / "www" / "mobile-forge"
    copied: list[Path] = []
    if not source_dir.exists():
        return copied
    target_dir.mkdir(parents=True, exist_ok=True)
    for asset in sorted(source_dir.iterdir()):
        if asset.is_file():
            target = target_dir / asset.name
            shutil.copy2(asset, target)
            copied.append(target)
    return copied


def fetch_sky_template() -> dict[str, Any]:
    local_template = REPO_ROOT / "templates" / "sky_system.yaml"
    if local_template.exists():
        parsed = yaml.safe_load(local_template.read_text(encoding="utf-8"))
        sky = (parsed or {}).get("button_card_templates", {}).get("sky_system")
        if isinstance(sky, dict):
            return sky

    request = urllib.request.Request(
        PASTEBIN_RAW,
        headers={
            "User-Agent": "Mozilla/5.0 HomeAssistant-MobileForge-Installer/1.0",
            "Accept": "text/plain,text/yaml,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        text = response.read().decode("utf-8", errors="replace")
    start = text.find("button_card_templates:")
    if start < 0:
        raise SystemExit("Pastebin loaded, but button_card_templates: was not found.")
    parsed = yaml.safe_load(text[start:])
    sky = (parsed or {}).get("button_card_templates", {}).get("sky_system")
    if not isinstance(sky, dict):
        raise SystemExit("Pastebin loaded, but button_card_templates.sky_system was not found.")
    return sky


def entity_ids(config_dir: Path) -> set[str]:
    registry = config_dir / ".storage" / "core.entity_registry"
    if not registry.exists():
        return set()
    try:
        raw = load_json(registry)
    except Exception:
        return set()
    return {entry.get("entity_id") for entry in raw.get("data", {}).get("entities", []) if entry.get("entity_id")}


def pick_entity(entities: set[str], preferred: list[str], contains: list[str], domain: str | None = None) -> str | None:
    for entity in preferred:
        if entity in entities:
            return entity
    haystack = sorted(entities)
    for entity in haystack:
        if domain and not entity.startswith(domain + "."):
            continue
        low = entity.lower()
        if all(term.lower() in low for term in contains):
            return entity
    return None


def find_navbar(cards: list[Any]) -> Any | None:
    for card in cards:
        if not isinstance(card, dict):
            continue
        card_type = str(card.get("type", ""))
        if "navbar-card" in card_type:
            return normalize_navbar(card)
    return None


def normalize_navbar(card: Any | None) -> Any | None:
    if not isinstance(card, dict):
        return None
    nav = copy.deepcopy(card)
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


def nav_spacer_card() -> dict[str, Any]:
    return {"type": "custom:button-card", "template": "mf_nav_spacer"}


def home_cards(view: dict[str, Any]) -> list[Any]:
    if isinstance(view.get("cards"), list):
        return view["cards"]
    if isinstance(view.get("sections"), list):
        cards: list[Any] = []
        for section in view["sections"]:
            if isinstance(section, dict) and isinstance(section.get("cards"), list):
                cards.extend(section["cards"])
        return cards
    return []


def set_home_cards(view: dict[str, Any], cards: list[Any]) -> None:
    view.pop("cards", None)
    view["type"] = "sections"
    view["max_columns"] = 1
    view["dense_section_placement"] = True
    view["sections"] = [
        {
            "type": "grid",
            "cards": cards,
        }
    ]


def button_template_styles(height: str = "72px") -> dict[str, Any]:
    return {
        "card": [
            f"height: {height}",
            f"min-height: {height}",
            "padding: 0",
            "border-radius: 22px",
            "border: 1px solid rgba(255,255,255,0.16)",
            "background: linear-gradient(145deg, rgba(34,31,39,0.82), rgba(15,17,24,0.62))",
            "box-shadow: 0 18px 42px rgba(0,0,0,0.22)",
            "backdrop-filter: blur(18px) saturate(1.1)",
            "overflow: hidden",
            "position: relative",
            "z-index: 2",
        ],
        "grid": [
            "grid-template-areas: 'icon label' 'icon value'",
            "grid-template-columns: 48px 1fr",
            "grid-template-rows: min-content min-content",
            "column-gap: 10px",
            "align-items: center",
            "height: 100%",
            "padding: 0 16px",
        ],
        "custom_fields": {
            "icon": [
                "grid-area: icon",
                "width: 42px",
                "height: 42px",
                "border-radius: 16px",
                "display: flex",
                "align-items: center",
                "justify-content: center",
                "background: rgba(255,255,255,0.12)",
            ],
            "label": [
                "grid-area: label",
                "justify-self: start",
                "font-size: 13px",
                "line-height: 16px",
                "font-weight: 650",
                "color: rgba(255,255,255,0.9)",
            ],
            "value": [
                "grid-area: value",
                "justify-self: start",
                "font-size: 12px",
                "line-height: 15px",
                "font-weight: 500",
                "color: rgba(255,255,255,0.68)",
            ],
        },
    }


def install_templates(dashboard: dict[str, Any], sky_template: dict[str, Any]) -> None:
    templates = dashboard.setdefault("button_card_templates", {})
    templates["sky_system"] = sky_template
    for template_file in sorted((REPO_ROOT / "templates").glob("*.yaml")):
        parsed = load_yaml(template_file)
        templates.update((parsed or {}).get("button_card_templates", {}))
    templates["sky_system"] = sky_template
    templates["mf_glass_tile"] = {
        "show_name": False,
        "show_icon": False,
        "show_state": False,
        "tap_action": {"action": "more-info"},
        "custom_fields": {
            "icon": """[[[
              const icon = variables.icon || 'mdi:home';
              const color = variables.color || '#ffd7a8';
              return `<ha-icon icon="${icon}" style="width:24px;height:24px;color:${color};"></ha-icon>`;
            ]]]""",
            "label": """[[[
              return variables.label || 'Status';
            ]]]""",
            "value": """[[[
              if (variables.value) return variables.value;
              if (!entity) return 'Ready';
              const state = entity.state === 'unavailable' ? 'Unavailable' : entity.state;
              return state.replace(/_/g, ' ');
            ]]]""",
        },
        "styles": button_template_styles(),
    }
    templates["mf_weather_panel"] = {
        "show_name": False,
        "show_icon": False,
        "show_state": False,
        "entity": "weather.forecast_home",
        "custom_fields": {
            "icon": """[[[
              const sunUp = states['sun.sun']?.state === 'above_horizon';
              const map = {
                sunny: sunUp ? 'mdi:white-balance-sunny' : 'mdi:weather-night',
                'clear-night': 'mdi:weather-night',
                partlycloudy: sunUp ? 'mdi:weather-partly-cloudy' : 'mdi:weather-night-partly-cloudy',
                cloudy: 'mdi:weather-cloudy',
                overcast: 'mdi:weather-cloudy',
                rainy: 'mdi:weather-rainy',
                pouring: 'mdi:weather-pouring',
                lightning: 'mdi:weather-lightning',
                snowy: 'mdi:weather-snowy',
                fog: 'mdi:weather-fog',
                windy: 'mdi:weather-windy'
              };
              return `<ha-icon icon="${map[entity.state] || 'mdi:weather-partly-cloudy'}" style="width:54px;height:54px;color:#ffe39a;filter:drop-shadow(0 8px 18px rgba(255,210,120,.35));"></ha-icon>`;
            ]]]""",
            "label": """[[[
              const temp = Math.round(entity.attributes.temperature ?? 0);
              const unit = entity.attributes.temperature_unit || 'deg';
              return `${temp}${unit}`;
            ]]]""",
            "value": """[[[
              const raw = entity.state || 'weather';
              const condition = raw.replace(/-/g, ' ').replace(/\\b\\w/g, c => c.toUpperCase());
              const humidity = entity.attributes.humidity;
              const wind = entity.attributes.wind_speed;
              return `${condition}${humidity ? ' - ' + humidity + '% humidity' : ''}${wind ? ' - ' + Math.round(wind) + ' wind' : ''}`;
            ]]]""",
        },
        "styles": {
            "card": [
                "height: 150px",
                "min-height: 150px",
                "padding: 0",
                "border-radius: 28px",
                "border: 1px solid rgba(255,255,255,0.18)",
                "background: linear-gradient(145deg, rgba(45,43,58,0.78), rgba(20,22,31,0.58))",
                "box-shadow: 0 22px 52px rgba(0,0,0,0.28)",
                "backdrop-filter: blur(20px) saturate(1.15)",
                "position: relative",
                "z-index: 2",
            ],
            "grid": [
                "grid-template-areas: 'icon label' 'icon value'",
                "grid-template-columns: 72px 1fr",
                "grid-template-rows: 1fr min-content",
                "column-gap: 14px",
                "align-items: center",
                "height: 100%",
                "padding: 0 22px",
            ],
            "custom_fields": {
                "icon": ["grid-area: icon", "align-self: center"],
                "label": [
                    "grid-area: label",
                    "align-self: end",
                    "justify-self: start",
                    "font-size: 46px",
                    "line-height: 48px",
                    "font-weight: 300",
                    "color: rgba(255,255,255,0.92)",
                ],
                "value": [
                    "grid-area: value",
                    "align-self: start",
                    "justify-self: start",
                    "font-size: 13px",
                    "line-height: 18px",
                    "color: rgba(255,255,255,0.68)",
                    "padding-top: 6px",
                ],
            },
        },
    }
    templates["mf_header"] = {
        "show_name": False,
        "show_icon": False,
        "show_state": False,
        "tap_action": {"action": "none"},
        "custom_fields": {
            "label": """[[[
              const h = new Date().getHours();
              const greeting = h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening';
              return `<div style="font-size:28px;line-height:32px;font-weight:750;color:white;">${greeting}, Michael</div>
                <div style="font-size:13px;line-height:18px;color:rgba(255,255,255,.68);margin-top:6px;">Mobile Forge is online</div>`;
            ]]]""",
        },
        "styles": {
            "card": [
                "height: 78px",
                "background: none",
                "border: none",
                "box-shadow: none",
                "padding: 10px 6px 0",
                "position: relative",
                "z-index: 2",
            ],
            "grid": ["grid-template-areas: 'label'", "height: 100%"],
            "custom_fields": {"label": ["grid-area: label", "justify-self: start", "align-self: center"]},
        },
    }


def card_background() -> dict[str, Any]:
    return {
        "type": "custom:button-card",
        "template": "sky_system",
        "tap_action": {"action": "none"},
        "hold_action": {"action": "none"},
    }


def glass_tile(entity: str | None, label: str, icon: str, color: str, value: str | None = None) -> dict[str, Any]:
    card = {
        "type": "custom:button-card",
        "template": "mf_glass_tile",
        "variables": {"label": label, "icon": icon, "color": color},
    }
    if entity:
        card["entity"] = entity
    if value:
        card["variables"]["value"] = value
    return card


def make_home_cards(config_dir: Path, navbar: Any | None) -> list[Any]:
    entities = entity_ids(config_dir)
    tesla_battery = pick_entity(
        entities,
        ["sensor.el_rocco_battery", "sensor.el_rocco_battery_level", "sensor.tesla_battery"],
        ["battery"],
        "sensor",
    ) or "sensor.el_rocco_battery_level"
    lights = pick_entity(entities, ["light.all_lights", "light.living_room_2", "light.living_room"], ["hue"], "light") or "light.living_room_2"
    security = pick_entity(
        entities,
        ["alarm_control_panel.nas_blink_home_security", "alarm_control_panel.blink", "alarm_control_panel.home_alarm", "alarm_control_panel.alarm"],
        ["blink"],
        "alarm_control_panel",
    ) or "alarm_control_panel.nas_blink_home_security"
    assistant = pick_entity(
        entities,
        ["update.home_assistant_core_update", "sensor.home_assistant_v2_db_size", "sensor.uptime"],
        ["home_assistant"],
        None,
    ) or "update.home_assistant_core_update"
    media = pick_entity(entities, ["media_player.living_room", "media_player.bedroom"], ["media_player"], None)

    cards: list[Any] = [
        card_background(),
        {
            "type": "custom:button-card",
            "template": "mf_page_title",
            "variables": {
                "title": "Home",
                "subtitle": "Animated sky, house status, and quick controls.",
            },
        },
        {
            "type": "custom:button-card",
            "template": "mf_hero",
            "entity": "weather.forecast_home",
            "variables": {
                "icon": "mdi:weather-partly-cloudy",
                "value": '[[[ return Math.round(entity?.attributes?.temperature ?? 56) + "°"; ]]]',
                "subtitle": (
                    '[[[ const raw = entity?.state || "clear night"; '
                    'const condition = raw.replace(/-/g, " "); '
                    'const humidity = entity?.attributes?.humidity; '
                    'const wind = entity?.attributes?.wind_speed; '
                    'return `${condition}${humidity ? " · " + humidity + "% humidity" : ""}${wind ? " · " + Math.round(wind) + " mph wind" : ""}`; ]]]'
                ),
                "accent_color": "rgba(255,211,164,0.96)",
            },
        },
        {
            "type": "grid",
            "columns": 2,
            "square": False,
            "cards": [
                mf_tile(
                    tesla_battery,
                    "El Rocco",
                    "mdi:car-electric",
                    "48%",
                    "charging",
                    "rgba(121,199,255,0.95)",
                    "/mobile-forge/tesla",
                    '[[[ const n = Number(entity?.state); return Number.isFinite(n) ? Math.round(n) + "%" : "48%"; ]]]',
                ),
                mf_tile(lights, "Lights", "mdi:lightbulb-group", "Ready", "rooms + scenes", "rgba(255,211,164,0.96)", "/mobile-forge/lights"),
                mf_tile(security, "Security", "mdi:shield-lock", "Armed", "front door clear", "rgba(157,226,182,0.95)", "/mobile-forge/security"),
                mf_tile(
                    assistant,
                    "Sebastian",
                    "mdi:home-assistant",
                    "Online",
                    "assistant ready",
                    "rgba(121,199,255,0.95)",
                    "/mobile-forge/house",
                    '[[[ return entity?.state === "off" ? "Online" : (entity?.state || "Online").replace(/_/g, " "); ]]]',
                ),
            ],
        },
        {
            "type": "horizontal-stack",
            "cards": [
                mf_pill("Cozy", "mdi:candle", "rgba(255,211,164,0.96)"),
                mf_pill("Movie", "mdi:movie-open", "rgba(121,199,255,0.95)"),
                mf_pill("Bright", "mdi:white-balance-sunny", "rgba(255,211,164,0.96)"),
                mf_pill("Sleep", "mdi:weather-night", "rgba(243,166,184,0.95)"),
            ],
        },
    ]
    if navbar:
        cards.append(nav_spacer_card())
        cards.append(navbar)
    return cards


def mf_tile(
    entity: str | None,
    title: str,
    icon: str,
    fallback_value: str,
    subtitle: str,
    accent: str,
    navigation_path: str | None = None,
    value_expr: str | None = None,
) -> dict[str, Any]:
    card: dict[str, Any] = {
        "type": "custom:button-card",
        "template": "mf_tile",
        "variables": {
            "icon": icon,
            "title": title,
            "value": value_expr or f'[[[ return entity?.state && entity.state !== "unavailable" ? entity.state.replace(/_/g, " ") : "{fallback_value}"; ]]]',
            "subtitle": subtitle,
            "accent_color": accent,
        },
    }
    if entity:
        card["entity"] = entity
    if navigation_path:
        card["tap_action"] = {"action": "navigate", "navigation_path": navigation_path}
    return card


def mf_pill(label: str, icon: str, accent: str) -> dict[str, Any]:
    return {
        "type": "custom:button-card",
        "template": "mf_pill",
        "variables": {
            "icon": icon,
            "label": label,
            "accent_color": accent,
        },
    }


def ensure_classic_view(dashboard: dict[str, Any], old_home: dict[str, Any], old_cards: list[Any]) -> None:
    views = dashboard.setdefault("views", [])
    views[:] = [view for view in views if view.get("path") != CLASSIC_VIEW_PATH]
    classic = {
        "title": "Forge Classic",
        "path": CLASSIC_VIEW_PATH,
        "icon": "mdi:archive-outline",
        "type": old_home.get("type", "sections"),
    }
    if old_home.get("sections"):
        classic["sections"] = copy.deepcopy(old_home["sections"])
        classic["max_columns"] = old_home.get("max_columns", 1)
    else:
        classic["cards"] = copy.deepcopy(old_cards)
    views.append(classic)


def assert_integrity(dashboard: dict[str, Any]) -> dict[str, Any]:
    views = dashboard.get("views")
    if not isinstance(views, list):
        raise SystemExit("Dashboard has no views list.")
    paths = [view.get("path") for view in views if isinstance(view, dict)]
    dupes = {path: count for path, count in Counter(paths).items() if count > 1}
    if dupes:
        raise SystemExit(f"Duplicate view paths after edit: {dupes}")
    home = next((view for view in views if view.get("path") == TARGET_VIEW_PATH), None)
    if not home:
        raise SystemExit("Home view is missing after edit.")
    cards = home_cards(home)
    has_sky = any(isinstance(card, dict) and card.get("type") == "custom:button-card" and card.get("template") == "sky_system" for card in cards)
    if not has_sky:
        raise SystemExit("Home view does not contain custom:button-card template: sky_system.")
    if cards and cards[0].get("template") != "sky_system":
        raise SystemExit("Home view first card is not template: sky_system.")
    if "sky_system" not in dashboard.get("button_card_templates", {}):
        raise SystemExit("button_card_templates.sky_system is missing after edit.")
    return {"paths": paths, "home_cards": cards, "home": home}


def cozy_home_exists(config_dir: Path) -> bool:
    storage_file = config_dir / ".storage" / "lovelace.cozy_home"
    if storage_file.exists():
        return True
    registry = config_dir / ".storage" / "lovelace_dashboards"
    if not registry.exists():
        return False
    try:
        items = load_json(registry).get("data", {}).get("items", [])
    except Exception:
        return False
    return any(item.get("id") == "cozy_home" or item.get("url_path") == "cozy-home" for item in items)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Wife Approved sky system into /mobile-forge/home.")
    parser.add_argument("--config-dir", default="/opt/ha-vps/homeassistant", help="Home Assistant config directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would change without writing.")
    args = parser.parse_args()

    config_dir = Path(args.config_dir).expanduser().resolve()
    if not config_dir.exists():
        raise SystemExit(f"Config dir does not exist: {config_dir}")

    source = discover_active_source(config_dir)
    dashboard, wrapper = load_dashboard(source)
    views = dashboard.get("views", [])
    home = next((view for view in views if isinstance(view, dict) and view.get("path") == TARGET_VIEW_PATH), None)
    if not home:
        raise SystemExit(f"Active dashboard has no view path: {TARGET_VIEW_PATH}")

    old_home = copy.deepcopy(home)
    old_cards = copy.deepcopy(home_cards(home))
    navbar = find_navbar(old_cards)
    old_count = len(old_cards)
    old_mtime = None
    changed_object = Path(source["file"] if source["mode"] == "yaml" else source["storage_file"])
    if changed_object.exists():
        old_mtime = changed_object.stat().st_mtime

    print("[1/7] Active dashboard source proved")
    print(f"  dashboard path: /{TARGET_DASHBOARD_PATH}")
    print(f"  mode: {source['mode']}")
    print(f"  source registry: {source['from']}")
    print(f"  changed object: {changed_object}")
    print(f"  Home view path: /{TARGET_DASHBOARD_PATH}/{TARGET_VIEW_PATH}")
    print(f"  old Home card count: {old_count}")

    print("[2/7] Fetching Reddit-linked Pastebin sky_system")
    sky_template = fetch_sky_template()

    print("[3/7] Building Wife Approved Mobile Forge Home view")
    install_templates(dashboard, sky_template)
    new_cards = make_home_cards(config_dir, navbar)
    set_home_cards(home, new_cards)
    ensure_classic_view(dashboard, old_home, old_cards)

    check = assert_integrity(dashboard)
    new_count = len(check["home_cards"])

    if args.dry_run:
        print("[4/7] Dry run requested; no files written")
        print(f"  new Home card count would be: {new_count}")
        return 0

    print("[4/7] Backing up active dashboard")
    backup = backup_source(source)
    print(f"  backup: {backup}")

    print("[5/7] Copying dashboard assets")
    for asset in copy_dashboard_assets(config_dir):
        print(f"  asset: {asset}")

    print("[6/7] Writing active dashboard")
    save_dashboard(source, dashboard, wrapper)

    print("[7/7] Re-loading written dashboard and verifying")
    reloaded, _ = load_dashboard(source)
    final = assert_integrity(reloaded)
    new_mtime = changed_object.stat().st_mtime if changed_object.exists() else None

    print("[8/8] Before/after summary")
    print(f"  active dashboard source: {changed_object}")
    print(f"  active dashboard path: /{TARGET_DASHBOARD_PATH}")
    print(f"  active Home view path: /{TARGET_DASHBOARD_PATH}/{TARGET_VIEW_PATH}")
    print(f"  old Home card count: {old_count}")
    print(f"  new Home card count: {len(final['home_cards'])}")
    print(f"  exact file/storage object changed: {changed_object}")
    print(f"  modified timestamp changed: {bool(old_mtime and new_mtime and new_mtime != old_mtime)}")
    print(f"  duplicate view paths: NONE")
    print(f"  /cozy-home exists: {cozy_home_exists(config_dir)}")
    print(f"  first Home card: {final['home_cards'][0].get('type')} template={final['home_cards'][0].get('template')}")
    print()
    print("Restart or reload Home Assistant dashboards now. If you use Docker:")
    print("  docker restart homeassistant")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
