"""outro_cta.py — cena de encerramento com mascote, CTA por plataforma, handle/QR.

params:
  cta_text (str, obrigatório)
  sub_cta (str, opt)
  handle (str, opt — sobrescreve brand.handle)
  qr (str, opt — caminho de PNG a exibir)
  mascot (bool, default true)
"""
from manim import (
    Text, ImageMobject, VGroup, Write, FadeIn, DOWN, UP, RIGHT, LEFT, ORIGIN,
)
from manim import config as manim_config

from .config_loader import ConfigScene


class OutroCtaScene(ConfigScene):
    """Cena de CTA final parametrizada."""

    def construct(self):
        cfg = self._load_config()
        params = cfg.get("params", {}) or {}
        cta_text = str(params.get("cta_text") or "Inscreva-se")
        sub_cta = params.get("sub_cta") or ""
        handle = params.get("handle") or self.THEME.get("handle", "")
        qr_path = params.get("qr") or ""
        use_mascot = bool(params.get("mascot", True))

        cta = Text(cta_text, font=self.font_sans,
                   font_size=64 if cfg.get("platform", "") != "yt-long" else 56,
                   line_spacing=0.85, color=self.accent)
        cta.scale_to_fit_width(min(cta.width, manim_config.frame_width * 0.80))
        cta.move_to(ORIGIN)

        sub = None
        if sub_cta:
            sub = Text(sub_cta, font=self.font_sans, font_size=26,
                       color=self.muted)
            sub.next_to(cta, DOWN, buff=0.45)
            sub.scale_to_fit_width(min(sub.width, manim_config.frame_width * 0.8))

        mascot = None
        if use_mascot:
            mascot = self._mascot(side="bottom_right", scale=0.5)
            if mascot is not None:
                self.add(mascot)

        handle_mobj = None
        if handle:
            handle_mobj = Text(handle, font=self.font_sans, font_size=24,
                               color=self.fg)
            handle_mobj.to_edge(UP, buff=0.35).to_edge(RIGHT, buff=0.4)

        qr = None
        if os_path_exists(qr_path):
            qr = ImageMobject(qr_path).scale(0.35)
            qr.to_edge(LEFT, buff=0.5).to_edge(DOWN, buff=0.5)

        self.play_timed(Write(cta), run_time=min(1.6, self.DURATION * 0.35))
        if sub:
            self.play_timed(FadeIn(sub, shift=0.4 * UP),
                            run_time=min(0.8, self.DURATION * 0.2))
        extras = [m for m in (handle_mobj, qr, mascot) if m is not None]
        if extras:
            self.play_timed(*(FadeIn(m) for m in extras),
                            run_time=min(0.8, self.DURATION * 0.15))
        self.finish_scene()


def os_path_exists(p):
    import os
    return bool(p) and os.path.exists(p)
