"""brand_frame.py — moldura/marca d'água/faixa de progresso/rótulo de capítulo.

params:
  chapter_label (str, opt)   rótulo do capítulo atual
  chapter_index (int, opt)   1-based
  chapter_total (int, opt)
  phase ("enter" | "full"), default "full" (moldura estática + micro animação)
"""
from manim import (
    Text, Rectangle, Line, RoundedRectangle, Create, FadeIn, VGroup, UP, DOWN,
    LEFT, RIGHT, ORIGIN, config as manim_config,
)

from .config_loader import ConfigScene


class BrandFrameScene(ConfigScene):
    """Moldura de marca parametrizada por plataforma — presente no compositor."""

    def construct(self):
        cfg = self._load_config()
        params = cfg.get("params", {}) or {}
        frame_cfg = self.THEME.get("frame", {}) or {}
        handle = self.THEME.get("handle", "")
        chapter_label = params.get("chapter_label") or ""
        chapter_index = params.get("chapter_index", 0)
        chapter_total = params.get("chapter_total", 0)

        frame_group = VGroup()

        if frame_cfg.get("progress_bar", False):
            bar = Rectangle(
                width=manim_config.frame_width * 0.7,
                height=0.06,
                fill_color=self.muted,
                fill_opacity=0.5,
                stroke_width=0,
            ).to_edge(UP, buff=0.35)
            progress = Rectangle(
                width=manim_config.frame_width * 0.7 * self._progress_fraction(
                    chapter_index, chapter_total),
                height=0.06,
                fill_color=self.accent,
                fill_opacity=1.0,
                stroke_width=0,
            ).to_edge(UP, buff=0.35).align_to(bar, LEFT)
            frame_group.add(bar, progress)

        if chapter_label and frame_cfg.get("chapter_label", False):
            chip = RoundedRectangle(
                corner_radius=0.1,
                width=max(len(chapter_label) * 0.13 + 0.3, 1.2),
                height=0.42,
                fill_color=self.accent2, fill_opacity=0.35,
                stroke_width=0,
            )
            chip.to_edge(UP, buff=0.65)
            chip_text = Text(chapter_label, font=self.font_sans, font_size=20,
                             color=self.fg).move_to(chip)
            frame_group.add(chip, chip_text)

        if handle and frame_cfg.get("watermark", False):
            wm = Text(handle, font=self.font_sans, font_size=18,
                      color=self.muted, opacity=0.75)
            wm.to_edge(RIGHT, buff=0.3).to_edge(UP, buff=0.3)
            frame_group.add(wm)

        self.play_timed(Create(frame_group), run_time=min(1.0, self.DURATION * 0.25))
        self.finish_scene()

    def _progress_fraction(self, index, total):
        try:
            if total and index:
                return max(0.05, min(1.0, float(index) / float(total)))
        except (TypeError, ZeroDivisionError):
            pass
        return 0.30
