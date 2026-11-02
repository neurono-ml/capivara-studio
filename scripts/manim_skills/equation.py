"""equation.py — MathTex com Write + transformações passo a passo + highlight.

params:
  latex (str, obrigatório)     equação inicial em LaTeX
  write_duration (float, opt)  duração da escrita (default 2.0)
  steps (list, opt)            [{"latex": str, "highlight": {"substring": str,
                                                      "color": "accent"}},
                               {"indicate": true}]
"""
from manim import (
    MathTex, Write, TransformMatchingTex, FadeOut, Create, Indicate,
    SurroundingRectangle,
)
from manim import config as manim_config

from .config_loader import ConfigScene


class EquationScene(ConfigScene):
    """Cena de equação parametrizada: escreve, transforma em steps, destaca trecho."""

    def construct(self):
        cfg = self._load_config()
        params = cfg.get("params", {}) or {}
        latex = params.get("latex") or r"E = mc^2"
        steps = params.get("steps") or []
        write_duration = float(params.get("write_duration", 2.0))

        current = MathTex(latex, font_size=42).set_color(self.fg)
        current.scale_to_fit_width(min(current.width, manim_config.frame_width * 0.85))
        self.play_timed(Write(current), run_time=write_duration)

        for step in steps:
            step_latex = step.get("latex")
            if not step_latex:
                continue
            highlight = step.get("highlight") or {}
            anims = []
            nxt = MathTex(step_latex, font_size=42).set_color(self.fg)
            nxt.scale_to_fit_width(min(nxt.width, manim_config.frame_width * 0.85))
            nxt.move_to(current)
            anims.append(TransformMatchingTex(current, nxt))
            hl_color = (self.accent
                        if highlight.get("color", "accent") == "accent"
                        else self.accent2)
            if highlight.get("substring"):
                try:
                    region = nxt.get_part_by_tex(highlight["substring"])
                    if region:
                        anims.append(Create(SurroundingRectangle(
                            region, color=hl_color, buff=0.18, corner_radius=0.08)))
                except (ValueError, IndexError):
                    pass
            if step.get("indicate"):
                anims.append(Indicate(current, color=self.accent))
            self.play_timed(*anims, run_time=max(float(step.get("duration", 2.0)), 0.8))
            current = nxt
            if self._elapsed >= self.DURATION - 0.5:
                break

        self.play_timed(FadeOut(current), run_time=0.7)
        self.finish_scene()
