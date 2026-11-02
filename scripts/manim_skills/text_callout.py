"""text_callout.py — texto de hook animado + mascote opcional.

params:
  text (str, obrigatório)
  position ("center" | "top" | "safe_bottom", default "center")
  highlight_words (list[str], opt)
  mascot (bool, default false)
  mascot_side ("bottom_right" | "bottom_left", default "bottom_right")
"""
from manim import (
    Text, Write, Create, FadeIn, FadeOut, SurroundingRectangle, UP, DOWN, ORIGIN,
)
from manim import config as manim_config

from .config_loader import ConfigScene


class TextCalloutScene(ConfigScene):
    """Cena de texto grande/hook parametrizada."""

    def construct(self):
        cfg = self._load_config()
        params = cfg.get("params", {}) or {}
        text = str(params.get("text") or "Sem texto")
        position = (params.get("position") or "center").lower()
        highlight_words = params.get("highlight_words") or []
        use_mascot = bool(params.get("mascot", False))
        mascot_side = params.get("mascot_side") or "bottom_right"

        # fonte escala: 9:16 cabe mais altura; 16:9 força width
        base_size = 48 if cfg.get("platform", "").startswith("yt") else 60
        heading = Text(text, font=self.font_sans, font_size=base_size,
                       line_spacing=0.9, color=self.fg)
        heading.scale_to_fit_width(min(heading.width, manim_config.frame_width * 0.82))

        if position == "top":
            heading.to_edge(UP, buff=0.8)
        elif position == "safe_bottom":
            heading.next_to(ORIGIN, DOWN, buff=1.4)
            heading.set_y(min(heading.get_y(), self._safe_y_center() - 0.5))
        else:
            heading.move_to(ORIGIN)

        # mascote entra antes (setup do frame)
        mascot = None
        if use_mascot:
            mascot = self._mascot(side=mascot_side, scale=0.45)
            if mascot is not None:
                self.add(mascot)

        self.play_timed(Write(heading), run_time=min(2.4, max(0.8, self.DURATION * 0.3)))

        # highlights sequenciais (palavras-chave)
        for word in highlight_words:
            try:
                sub = heading.get_parts_by_text(word)  # Text API: lista de glyphs
            except AttributeError:
                sub = None
            if sub:
                for glyph in sub:
                    rect = SurroundingRectangle(glyph, color=self.accent, buff=0.06,
                                                corner_radius=0.04)
                    self.play_timed(Create(rect), run_time=0.35)
                # única passada de highlight por palavra para economizar loop
        self.finish_scene()
