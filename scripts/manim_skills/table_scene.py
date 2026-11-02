"""table_scene.py — tabela com entrada linha-a-linha e highlight de células.

params:
  headers (list[str], obrigatório)
  rows (list[list[str]], obrigatório)
  highlight_cells (list[[row, col]] 0-based sem header, opt)
  row_reveal_duration (float, default 0.8)
"""
from manim import (
    Table, Create, SurroundingRectangle, VGroup, ORIGIN,
    config as manim_config,
)

from .config_loader import ConfigScene

_HEADER_LINES_TIME = 0.3


def _colorize(table, fg):
    """Aplica cor do tema ao texto de células."""
    for entry in table.get_entries():
        try:
            entry.set_color(fg)
        except AttributeError:
            pass


class TableScene(ConfigScene):
    """Cena de tabela parametrizada."""

    def construct(self):
        cfg = self._load_config()
        params = cfg.get("params", {}) or {}
        headers = params.get("headers") or []
        rows = params.get("rows") or []
        highlights = params.get("highlight_cells") or []
        row_reveal = max(float(params.get("row_reveal_duration", 0.8)), 0.25)

        if not rows and not headers:
            rows = [["..."]]

        def as_str(x):
            return x if isinstance(x, str) else str(x)

        data = ([headers] if headers else []) + [[as_str(c) for c in r] for r in rows]

        table = Table(
            data,
            include_outer_lines=True,
            line_config={"color": self.muted, "stroke_width": 1.2},
        )
        _colorize(table, self.fg)
        table.scale_to_fit_width(min(table.width, manim_config.frame_width * 0.85))
        table.scale_to_fit_height(min(table.height, manim_config.frame_height * 0.62))
        table.move_to(ORIGIN)

        n_header = 1 if headers else 0

        if n_header:
            header_row = table.get_rows()[0]
            self.play_timed(Create(header_row), run_time=0.8)
            self.play_timed(Create(VGroup(*table.get_vertical_lines()[:2])),
                            run_time=_HEADER_LINES_TIME)

        for ri in range(n_header, len(data)):
            self.play_timed(Create(table.get_rows()[ri]), run_time=row_reveal)

        for (r, c) in highlights:
            try:
                cell = table.get_entries((int(r) + n_header, int(c)))
            except (IndexError, ValueError, KeyError):
                continue
            rect = SurroundingRectangle(cell, color=self.accent, buff=0.08,
                                        corner_radius=0.05)
            self.play_timed(Create(rect), run_time=0.45)

        self.finish_scene()
