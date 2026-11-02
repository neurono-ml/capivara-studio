"""matrix_scene.py — matriz com entrada + transformação destacada.

params:
  latex_main (str, obrigatório)   LaTeX da matriz inicial (bmatrix etc.)
  transform (obj, opt)            {"latex": str, "kind": "translate"|"rotate"|"scale",
                                   "shift": [x, y, z]}
"""
import math

from manim import (
    MathTex, Write, Transform, TransformMatchingTex, Create,
    SurroundingRectangle, FadeOut,
)
from manim import config as manim_config

from .config_loader import ConfigScene


class MatrixScene(ConfigScene):
    """Cena de matriz parametrizada."""

    def construct(self):
        cfg = self._load_config()
        params = cfg.get("params", {}) or {}
        latex_main = params.get("latex_main") or \
            r"\begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix}"
        transform = params.get("transform") or None

        main = MathTex(latex_main, font_size=40).set_color(self.fg)
        main.scale_to_fit_width(min(main.width, manim_config.frame_width * 0.8))
        self.play_timed(Write(main), run_time=2.0)

        if transform:
            tr_latex = transform.get("latex")
            kind = (transform.get("kind") or "translate").lower()
            if tr_latex:
                nxt = MathTex(tr_latex, font_size=40).set_color(self.fg)
                nxt.scale_to_fit_width(min(nxt.width, manim_config.frame_width * 0.8))
                nxt.move_to(main)
            else:
                nxt = main

            if kind == "rotate":
                rotated = main.copy().rotate(math.pi / 4)
                rotated.move_to(ORIGIN)
                rotated.scale_to_fit_width(
                    min(rotated.width, manim_config.frame_width * 0.8))
                if tr_latex:
                    self.play_timed(Transform(main, rotated), run_time=1.2)
                    self.play_timed(TransformMatchingTex(rotated, nxt), run_time=1.2)
                else:
                    self.play_timed(Transform(main, rotated), run_time=1.4)
            elif kind == "scale":
                grown = main.copy().scale(1.4)
                grown.move_to(ORIGIN)
                grown.scale_to_fit_width(
                    min(grown.width, manim_config.frame_width * 0.8))
                if tr_latex:
                    self.play_timed(Transform(main, grown), run_time=1.2)
                    self.play_timed(TransformMatchingTex(grown, nxt), run_time=1.2)
                else:
                    self.play_timed(Transform(main, grown), run_time=1.4)
            else:  # translate (ou tipo desconhecido)
                if tr_latex:
                    self.play_timed(TransformMatchingTex(main, nxt), run_time=1.4)
                    shift = transform.get("shift") or [0.6, -0.3, 0]
                    echo = nxt.copy().set_color(self.accent2).shift(shift)
                    self.play_timed(Create(echo), run_time=0.8)
                    self.play_timed(FadeOut(echo), run_time=0.4)
                else:
                    shift = [0.6, -0.3, 0]
                    self.play_timed(main.animate.shift(shift), run_time=1.2)

            hl = transform.get("highlight") or {}
            if hl.get("substring"):
                try:
                    region = nxt.get_part_by_tex(hl["substring"])
                    if region:
                        self.play_timed(Create(SurroundingRectangle(
                            region, color=self.accent, buff=0.12,
                            corner_radius=0.06)), run_time=0.5)
                except (ValueError, IndexError):
                    pass

        self.finish_scene()
