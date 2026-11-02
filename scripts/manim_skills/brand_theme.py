"""brand_theme — carrega THEME (paleta/fontes/mascote) do brand JSON.

brand.local.json vive no host (volume read-only em /work/brand/). As cenas nunca
contêm cores hardcoded: tudo vem daqui, com override pelo config da cena.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# fallback explícito para o brand.example.json da skill (dentro do container:
# montado por docker-run.sh; no build é copiado junto com scripts/)
_FALLBACK_CANDIDATES = (
    "/work/templates/brand.example.json",
    "/work/brand/brand.example.json",
    Path(__file__).resolve().parents[1].parent / "templates" / "brand.example.json",
)

DEFAULT_LIGHT_COLORS = {
    "bg": "#0B0F1A",
    "fg": "#F5F5F5",
    "accent": "#FFD166",
    "accent2": "#7B5EA7",
    "muted": "#8B93A7",
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def resolve_brand_path(config: Dict[str, Any]) -> Optional[str]:
    """Resolve o caminho do brand JSON a partir do config da cena."""
    brand_field = config.get("brand")
    if brand_field and os.path.exists(brand_field):
        return brand_field
    for cand in _FALLBACK_CANDIDATES:
        if str(cand) and os.path.exists(str(cand)):
            return str(cand)
    return None


def load_brand(config: Dict[str, Any]) -> Dict[str, Any]:
    """Carrega THEME: brand JSON (config ou fallback) + defaults genéricos.

    Retorna dict com keys: palette, fonts, mascot, handle, frame, voice, path.
    Nunca lê nada pessoal fora do JSON apontado.
    """
    theme: Dict[str, Any] = {
        "palette": dict(DEFAULT_LIGHT_COLORS),
        "fonts": {"sans": "Noto Sans", "mono": "Noto Sans Mono"},
        "mascot": {"path": "", "emoji": ""},
        "handle": "",
        "frame": {"progress_bar": False, "watermark": False, "chapter_label": False},
        "voice": {},
        "path": None,
    }
    brand_path = resolve_brand_path(config)
    if brand_path:
        try:
            with open(brand_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            theme = _deep_merge(theme, data)
            theme["path"] = brand_path
        except (OSError, json.JSONDecodeError) as exc:
            # cenas não devem falhar por brand ausente: seguem com defaults
            print(f"[brand_theme] aviso: brand '{brand_path}' inválido ({exc}); usando fallback genérico")
    # override direto no config da cena ganha sobre o brand (cena > marca)
    if isinstance(config.get("theme_override"), dict):
        theme = _deep_merge(theme, {"$": config["theme_override"]})["$"]
    return theme


def hex_color(theme: Dict[str, Any], key: str, fallback: str = "#FFFFFF"):
    """Helper: cor hex → objeto cor aceito por Manim (string hex funciona)."""
    palette = theme.get("palette", {})
    return palette.get(key, fallback) or fallback


def mascot_path(theme: Dict[str, Any]) -> str:
    m = theme.get("mascot", {})
    p = m.get("path") or ""
    if p and os.path.exists(p):
        return p
    return ""


def mascot_emoji(theme: Dict[str, Any]) -> str:
    return (theme.get("mascot", {}) or {}).get("emoji", "") or ""
