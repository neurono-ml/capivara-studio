"""config_loader — mixin base das cenas: carrega config JSON + THEME do brand.

Convenção OBRIGATÓRIA de todas as cenas do manim_skills:
  * classe estende ConfigScene (que estende manim.Scene);
  * config chega por variável de ambiente `SCENE_CONFIG` (caminho do JSON),
    injetada pelo render_manim.py antes de `manim render`;
  * zero conteúdo hardcoded: cores/fontes/mascote vêm do brand;
  * duração total da cena = cfg["duration"]; cenas chamam self.finish_scene()
    no fim do construct() para preencher o tempo restante com wait().
"""
import json
import os

from manim import Scene, config as manim_config

from .brand_theme import load_brand, hex_color, mascot_path, mascot_emoji

SCENE_CONFIG_ENV = "SCENE_CONFIG"


class ConfigScene(Scene):
    """Base para cenas parametrizadas."""

    #: estilo de capítulo/rótulo por plataforma (safe areas, ver scene_director)
    SAFE_TOP_PX = 200
    SAFE_BOTTOM_PX = 250

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cfg: dict = {}
        self.THEME: dict = {}
        self.DURATION: float = 5.0
        self._elapsed: float = 0.0

    # ------------------------------------------------------------------ config
    def _load_config(self) -> dict:
        """Lê o JSON da variável de ambiente SCENE_CONFIG e prepara THEME/tema."""
        path = os.environ.get(SCENE_CONFIG_ENV, "")
        if not path or not os.path.exists(path):
            raise RuntimeError(
                f"cena sem config: defina {SCENE_CONFIG_ENV}=<caminho do json>"
            )
        with open(path, "r", encoding="utf-8") as fh:
            self.cfg = json.load(fh)
        self.THEME = load_brand(self.cfg)
        self.DURATION = max(float(self.cfg.get("duration", 5.0)), 0.3)
        self.camera.background_color = hex_color(self.THEME, "bg", "#0B0F1A")
        return self.cfg

    # ------------------------------------------------------------------ helpers
    @property
    def accent(self):
        return hex_color(self.THEME, "accent", "#FFD166")

    @property
    def accent2(self):
        return hex_color(self.THEME, "accent2", "#7B5EA7")

    @property
    def fg(self):
        return hex_color(self.THEME, "fg", "#F5F5F5")

    @property
    def muted(self):
        return hex_color(self.THEME, "muted", "#8B93A7")

    @property
    def font_sans(self):
        return self.THEME.get("fonts", {}).get("sans", "Noto Sans")

    @property
    def font_mono(self):
        return self.THEME.get("fonts", {}).get("mono", "Noto Sans Mono")

    def play_timed(self, *anims, run_time=None, **kwargs):
        """self.play() que rastreia o tempo gasto em animações."""
        if run_time is None:
            total = sum(getattr(a, "run_time", getattr(a, "duration", 0.0)) or 0.0
                        for a in anims)
            run_time = max(total, 0.5)
        self._elapsed += float(run_time)
        self.play(*anims, run_time=run_time, **kwargs)

    def _safe_y_center(self) -> float:
        """Centro vertical útil (evita áreas cortadas pela UI em 9:16)."""
        h = manim_config.pixel_height
        top = self.SAFE_TOP_PX / h
        bottom = self.SAFE_BOTTOM_PX / h
        return (bottom + (1 - top)) / 2.0

    def _mascot(self, side="bottom_right", scale=0.5):
        """Mobject do mascote se houver PNG com alpha; caso contrário vazio."""
        from manim import ImageMobject, Text, DR, DL, ORIGIN
        p = mascot_path(self.THEME)
        if p:
            img = ImageMobject(p).scale(scale)
        else:
            emoji = mascot_emoji(self.THEME)
            if not emoji:
                return None
            img = Text(emoji, font=self.font_sans).scale(scale)
        if side == "bottom_right":
            img.to_corner(DR)
        elif side == "bottom_left":
            img.to_corner(DL)
        else:
            img.move_to(ORIGIN)
        return img

    def finish_scene(self):
        """Preenche o tempo restante até a duração alvo da cena."""
        remaining = self.DURATION - self._elapsed
        if remaining > 0:
            self.wait(remaining)
