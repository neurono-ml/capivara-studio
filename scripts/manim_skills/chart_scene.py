"""chart_scene.py — graficos bar/line/pie com contagem animada.

params:
  kind ("bar" | "line" | "pie", obrigatorio)
  labels (list[str], obrigatorio)
  values (list[float], obrigatorio)
  accent_bar (int 0-based, opt)
  animate_count (bool, default true)
  show_axis (bool, default true)
"""
import numpy as np

from manim import (
    Axes, Create, Dot, DOWN, UP, ORIGIN, FadeIn, GrowFromEdge, Line, Rectangle,
    RIGHT, Sector, Text, VGroup,
)
from manim import config as manim_config

from .config_loader import ConfigScene


def _fmt(value):
    """Formata numero de forma compacta para rotulo."""
    return f"{round(float(value), 2):g}"


class _ChartBase(ConfigScene):
    """Base comum aos tres tipos de grafico."""

    def _read_cfg(self):
        params = self.cfg.get("params", {}) or {}
        self.labels = list(params.get("labels") or ["A"])
        self.values = list(params.get("values") or [1])
        if len(self.values) != len(self.labels):
            raise ValueError("chart: len(labels) != len(values)")
        if not all(isinstance(v, (int, float)) for v in self.values):
            raise ValueError("chart: values precisam ser numericos")
        self.accent_bar = params.get("accent_bar", None)
        self.animate_count = bool(params.get("animate_count", True))
        self.show_axis = bool(params.get("show_axis", True))

    def _bar_color(self, i):
        return self.accent if i == self.accent_bar else self.accent2

    def _count_label(self, value):
        return Text(_fmt(value), font=self.font_sans, font_size=26, color=self.fg)


class ChartBarScene(_ChartBase):
    """Barras crescendo de baixo para cima com rotulos de contagem."""

    def construct(self):
        self._load_config()
        self._read_cfg()

        n = len(self.values)
        width = manim_config.frame_width * 0.90
        height = manim_config.frame_height * 0.55
        base_y = -height / 2.0
        slot = width / max(n, 1)
        bar_w = slot * 0.55
        max_val = max(abs(v) for v in self.values) or 1.0

        if self.show_axis:
            axis = VGroup(
                Line([-width / 2, base_y, 0], [width / 2, base_y, 0],
                     color=self.muted, stroke_width=1.5),
                Line([-width / 2, base_y, 0], [-width / 2, base_y + height, 0],
                     color=self.muted, stroke_width=1.5),
            )
            self.play_timed(Create(axis), run_time=0.6)

        per_item = max((self.DURATION - self._elapsed - 0.4) / max(n, 1), 0.3)
        for i, value in enumerate(self.values):
            x_c = -width / 2.0 + slot * (i + 0.5)
            bar_h = max((value / max_val) * height, 0.02)
            bar = Rectangle(
                width=bar_w,
                height=bar_h,
                fill_color=self._bar_color(i),
                fill_opacity=0.92,
                stroke_width=0,
            )
            bar.move_to([x_c, base_y + bar_h / 2.0, 0])
            self.play_timed(GrowFromEdge(bar, DOWN), run_time=per_item * 0.55)

            count = self._count_label(value).next_to(bar, UP, buff=0.15)
            if self.animate_count:
                self.play_timed(FadeIn(count, scale=0.6),
                                run_time=per_item * 0.25)

            axis_base = np.array([x_c, base_y, 0.0])
            lbl = Text(self.labels[i], font=self.font_sans, font_size=22,
                       color=self.muted).next_to(axis_base, DOWN, buff=0.2)
            self.play_timed(FadeIn(lbl), run_time=per_item * 0.2)

        self.finish_scene()


class ChartLineScene(_ChartBase):
    """Linha sobre Axes com pontos e rotulos revelados em sequencia."""

    def construct(self):
        self._load_config()
        self._read_cfg()

        max_val = max(self.values) or 1.0
        n = len(self.values)
        axes = Axes(
            x_range=[0, max(n - 1, 1), max(n - 1, 1)],
            y_range=[0, max_val * 1.15, max(max_val / 2, 0.5)],
            x_length=manim_config.frame_width * 0.78,
            y_length=manim_config.frame_height * 0.52,
            axis_config={"color": self.muted, "stroke_width": 1.5},
            tips=False,
        )
        if self.show_axis:
            self.play_timed(Create(axes), run_time=0.8)

        points = [axes.c2p(i, float(v)) for i, v in enumerate(self.values)]
        graph = VGroup(*[
            Line(points[i], points[i + 1],
                 color=self.accent2, stroke_width=3.0)
            for i in range(len(points) - 1)
        ])
        self.play_timed(Create(graph),
                        run_time=min(max(self.DURATION * 0.25, 1.0), 3.0))

        per_pt = max((self.DURATION - self._elapsed - 0.3) / max(n, 1), 0.2)
        for i, value in enumerate(self.values):
            anims = [FadeIn(Dot(axes.c2p(i, value), radius=0.07,
                                color=self.accent), scale=0.5)]
            if self.animate_count:
                count = self._count_label(value).next_to(
                    axes.c2p(i, value), UP, buff=0.18)
                anims.append(FadeIn(count))
            self.play_timed(*anims, run_time=per_pt)

        self.finish_scene()


class ChartPieScene(_ChartBase):
    """Pizza com setores desenhados em sequencia + legenda alinhada a direita."""

    def construct(self):
        self._load_config()
        self._read_cfg()

        total = sum(self.values) or 1.0
        radius = min(manim_config.frame_height * 0.28,
                     manim_config.frame_width * 0.22)
        bg = self.THEME.get("palette", {}).get("bg", "#0B0F1A")
        colors = [self.accent, self.accent2, self.muted]

        per_item = max((self.DURATION - self._elapsed - 0.4) / max(len(self.values), 1), 0.3)
        start = 0.0
        for i, value in enumerate(self.values):
            angle = (value / total) * 2.0 * np.pi
            sector = Sector(
                outer_radius=radius,
                angle=angle + 1e-9,
                start_angle=start,
                stroke_width=1.0,
                stroke_color=bg,
                fill_color=self._bar_color(i),
                fill_opacity=0.92,
            )
            sector.move_to(ORIGIN)
            self.play_timed(Create(sector), run_time=per_item * 0.55)
            start += angle

        legend = VGroup()
        for i, value in enumerate(self.values):
            swatch = Rectangle(width=0.22, height=0.22,
                               fill_color=self._bar_color(i),
                               fill_opacity=1.0, stroke_width=0)
            txt = Text(f"{self.labels[i]} · {_fmt(value)}",
                       font=self.font_sans, font_size=22, color=self.fg)
            legend.add(VGroup(swatch, txt).arrange(RIGHT, buff=0.12))

        legend.arrange(DOWN, aligned_edge=RIGHT, buff=0.15)
        legend.move_to([manim_config.frame_width * 0.22, 0.0, 0.0])

        per_legend = max((self.DURATION - self._elapsed - 0.3) / max(len(self.values), 1), 0.2)
        for row in legend:
            self.play_timed(FadeIn(row), run_time=per_legend)

        self.finish_scene()
