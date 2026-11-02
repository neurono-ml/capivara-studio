#!/usr/bin/env python3
"""render_manim.py — CLI de renderização de cenas DENTRO do container.

Recebe --config (um JSON de cena ou diretório com vários) e, para cada config:
  1. valida campos mínimos;
  2. resolve a classe de cena apropriada por scene_type (registry);
  3. gera um "snippet" module-level (para descoberta de cena pelo `manim render`);
  4. roda `manim render` em subprocess com SCENE_CONFIG=<json> no ambiente;
  5. coleta o arquivo de saída (MP4/PNG), escreve per-scene results.json.

NÃO há conteúdo hardcoded: tudo vem dos configs. Idempotência por hash é deixada
para o orquestrador (SKILL.md — Etapa 4).

uso:
  render_manim.py --config /work/output/<sid>/scenes/            # Diretório
  render_manim.py --config /work/output/<sid>/scenes/seg001.json # isolado
  render_manim.py --config dir --out /work/output/scenes_out --skip-failed
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_OUT = "/work/output/scenes_out"
SNIPPET_TEMPLATE = '''\
from manim import config as _mconfig
_mconfig.pixel_width = {pixel_width}
_mconfig.pixel_height = {pixel_height}
_mconfig.frame_rate = {frame_rate}
_mconfig.save_last_frame = {is_png}
_mconfig.background_color = "{bg}"
_mconfig.output_file = "{out_basename}"
_mconfig.disable_caching = False
from manim_skills.registry import get_scene_class
_Scene = get_scene_class({scene_type!r}, {chart_kind!r})
_ClsName = "RenderedScene"
exec(f"class {{_ClsName}}(_Scene): pass")
'''


def load_configs(config_arg):
    p = Path(config_arg)
    if p.is_file():
        return [p]
    if p.is_dir():
        files = sorted(p.glob("*.json"))
        # ignora arquivos auxiliares (manifest, results, plano)
        return [f for f in files if f.name not in ("manifest.json", "results.json")]
    raise FileNotFoundError(f"--config não encontrado: {config_arg}")


def validate(cfg):
    required = ("id", "scene_type", "resolution", "duration", "platform")
    missing = [k for k in required if k not in cfg]
    if missing:
        raise ValueError(f"campos faltando no config: {missing}")
    w, h = cfg["resolution"]
    if not (isinstance(w, int) and isinstance(h, int) and w > 0 and h > 0):
        raise ValueError("resolution inválida")
    if float(cfg["duration"]) <= 0:
        raise ValueError("duration deve ser > 0")


def resolve_scene_type(cfg):
    scene_type = cfg["scene_type"]
    chart_kind = ""
    if scene_type == "chart":
        chart_kind = (cfg.get("params", {}) or {}).get("kind", "bar")
        if chart_kind not in ("bar", "line", "pie"):
            raise ValueError(f"chart kind inválido: {chart_kind}")
    return scene_type, chart_kind


def render_one(cfg_path, out_dir, keep_partial=False):
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    validate(cfg)
    scene_type, chart_kind = resolve_scene_type(cfg)

    w, h = cfg["resolution"]
    is_png = cfg.get("output_format") == "png" or cfg["platform"] == "ig_carousel"
    out_basename = f"{cfg['id']}"
    bg = "#000000"

    with tempfile.TemporaryDirectory(prefix="capy-manim-") as td:
        snippet = SNIPPET_TEMPLATE.format(
            pixel_width=w, pixel_height=h, frame_rate=cfg.get("frame_rate", 30),
            is_png=str(bool(is_png)), bg=bg, out_basename=out_basename,
            scene_type=scene_type, chart_kind=chart_kind,
        )
        snippet_path = Path(td) / "scene_snippet.py"
        snippet_path.write_text(snippet, encoding="utf-8")

        env = os.environ.copy()
        env["SCENE_CONFIG"] = str(cfg_path.resolve())
        env["PYTHONPATH"] = "/work/scripts:" + env.get("PYTHONPATH", "")
        env.setdefault("HOME", "/tmp")  # tlmgr/pdflatex exigem HOME

        cmd = [
            "manim", "render",
            str(snippet_path), "RenderedScene",
            "--media_dir", str(Path(td) / "media"),
            "-v", "WARNING",
        ]
        if is_png:
            cmd.append("--save_last_frame")

        proc = subprocess.run(cmd, env=env, capture_output=True, text=True,
                              timeout=cfg.get("render_timeout_s", 600))
        result = {
            "id": cfg["id"],
            "scene_type": scene_type,
            "config": str(cfg_path),
            "config_sha256": hashlib.sha256(cfg_path.read_bytes()).hexdigest(),
            "resolution": cfg["resolution"],
            "duration": cfg["duration"],
            "platform": cfg["platform"],
            "returncode": proc.returncode,
        }
        if proc.returncode == 0:
            # manim escreve em <media_dir>/videos/<arquivo>/<qualidade>/<output>";
            # procuramos tanto no out_dir quanto no media_dir
            search_roots = [Path(out_dir), Path(td) / "media"]
            real = []
            for root in search_roots:
                real += [c for c in root.rglob(f"{out_basename}.*")
                         if c.suffix in (".mp4", ".png", ".mov", ".webm")]
            real = sorted(real, key=lambda p: p.stat().st_mtime, reverse=True)
            if real:
                import shutil
                final = Path(out_dir) / real[0].name
                if real[0] != final:
                    shutil.move(str(real[0]), str(final))
                result["video_path"] = str(final.resolve())
                result["output_format"] = ("png" if final.suffix == ".png"
                                           else "video")
                result["status"] = "success"
            else:
                result["status"] = "failed"
                result["error"] = "output não encontrada"
        else:
            result["status"] = "failed"
        result["stderr_tail"] = "\n".join((proc.stderr or "").splitlines()[-15:])
        return result


def main():
    ap = argparse.ArgumentParser(description="Render de cenas Manim por config JSON")
    ap.add_argument("--config", required=True,
                    help="caminho de um JSON de cena ou diretório com vários")
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="diretório de saída dos MP4/PNGs")
    ap.add_argument("--skip-failed", action="store_true",
                    help="somente registra falhas; não interrompe o lote")
    ap.add_argument("--results", default=None,
                    help="caminho do results.json (default: <out>/results.json)")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = Path(args.results) if args.results else out_dir / "results.json"

    configs = load_configs(args.config)
    # mesmo diretório deve ignorar o próprio results.json de lote anterior
    results = []
    any_fatal = False
    for cfg_path in configs:
        if cfg_path.name == results_path.name:
            continue
        try:
            res = render_one(cfg_path, str(out_dir))
        except Exception as exc:  # noqa: BLE001 — worker não deve abortar o lote
            res = {
                "id": cfg_path.stem,
                "config": str(cfg_path),
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            }
        results.append(res)
        status_icon = "OK  " if res["status"] == "success" else "FAIL"
        print(f"[{status_icon}] {res['id']} ({res.get('scene_type', '?')}) "
              f"-> {res.get('video_path', res.get('error', ''))}", flush=True)

    # merge com results.json existente (idempotência incremental)
    existing = {"results": []}
    if results_path.exists():
        try:
            existing = json.loads(results_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {"results": []}
    prev = {r.get("id"): r for r in existing.get("results", [])}
    for r in results:
        prev[r.get("id")] = r
    results_path.write_text(
        json.dumps({"results": list(prev.values())}, indent=2, ensure_ascii=False),
        encoding="utf-8")

    failures = [r for r in results if r.get("status") != "success"]
    print(f"concluído: {len(results) - len(failures)} ok, {len(failures)} falha "
          f"(results.json: {results_path})")
    return 0 if (not failures or args.skip_failed) else 1


if __name__ == "__main__":
    sys.exit(main())
