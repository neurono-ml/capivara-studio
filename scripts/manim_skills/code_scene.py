"""code_scene.py — bloco de código com reveal (typewriter/línea-a-línea) + destaque.

params:
  code (str, obrigatório)
  language (str, obrigatório)
  mode ("typewriter" | "lines", default "lines")
  highlight_lines (list[int] 0-based, opt)
  comment_popup (str, opt)
  theme_dark (bool, default true)
"""
from manim import (
    Code, Create, Write, Text, FadeIn, UL, DOWN, SurroundingRectangle,
    config as manim_config, VGroup,
)

from .config_loader import ConfigScene


class CodeScene(ConfigScene):
    """Cena de código parametrizada, tema compatível com fundo escuro."""

    def construct(self):
        cfg = self._load_config()
        params = cfg.get("params", {}) or {}
        code_str = params.get("code") or "print('')"
        language = params.get("language") or "python"
        mode = params.get("mode") or "lines"
        highlight_lines = params.get("highlight_lines") or []
        comment_popup = params.get("comment_popup") or ""
        theme_dark = bool(params.get("theme_dark", True))

        code_mobj = Code(
            code=code_str,
            language=language,
            font_size=18,
            style="monokai" if theme_dark else "default",
            background="rectangle",
            background_stroke_color=self.muted,
            background_stroke_width=1.0,
            corner_radius=0.1,
            insert_line_no=False,
        )

        n_lines = max(len(code_str.strip().splitlines()), 1)

        if mode == "typewriter":
            self.play_timed(Write(code_mobj),
                            run_time=min(max(1.5, 0.12 * n_lines), 6.0))
        else:
            self.play_timed(Create(code_mobj), run_time=1.0)
            per_line = self._budget_per_line(n_lines)
            lines = self._get_code_lines(code_mobj)
            for i in range(n_lines):
                line = lines[i] if i < len(lines) else None
                if line is not None:
                    self.play_timed(FadeIn(line, shift=0.1 * UL),
                                    run_time=max(per_line, 0.15))
                else:
                    self.wait(max(per_line, 0.15))

        for li in highlight_lines:
            lines = self._get_code_lines(code_mobj)
            if 0 <= int(li) < len(lines):
                rect = SurroundingRectangle(lines[int(li)], color=self.accent,
                                            buff=0.08, corner_radius=0.04)
                self.play_timed(Create(rect), run_time=0.5)

        if comment_popup:
            popup = Text(comment_popup, font=self.font_sans, font_size=24,
                         color=self.fg).to_edge(DOWN)
            self.play_timed(FadeIn(popup, shift=0.3 * UL), run_time=0.6)

        self.finish_scene()

    def _get_code_lines(self, code_mobj):
        """Recupera linha-a-linha do Code (API varia entre versões do Manim)."""
        lines = getattr(code_mobj, "code", None)
        if lines is None:
            try:
                lines = code_mobj.submobjects[1]
            except (IndexError, AttributeError):
                lines = None
        if lines is None:
            return VGroup()
        try:
            return list(lines)
        except TypeError:
            return VGroup()

    def _budget_per_line(self, n_lines: int) -> float:
        """Distribui o tempo restante entre as linhas para respeitar DURATION."""
        budget = max(self.DURATION - self._elapsed - 0.8, 0.4)
        return min(budget / max(n_lines, 1), 0.9)
