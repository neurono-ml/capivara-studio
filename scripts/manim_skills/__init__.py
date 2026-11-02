"""manim_skills — cenas Manim 0.18.x parametrizadas por config JSON.

Cada Scene carrega seu config via self._load_config() (arquivo JSON apontado por
--config do CLI, embutido pelo render_manim.py). Zero conteúdo hardcoded.
Tema (cores, fontes, mascote) vem do brand JSON referenciado no config.
"""
from .brand_theme import load_brand  # noqa: F401
from .registry import get_scene_class  # noqa: F401
from .equation import EquationScene  # noqa: F401
from .code_scene import CodeScene  # noqa: F401
from .table_scene import TableScene  # noqa: F401
from .matrix_scene import MatrixScene  # noqa: F401
from .chart_scene import ChartBarScene, ChartLineScene, ChartPieScene  # noqa: F401
from .diagram_scene import DiagramScene  # noqa: F401
from .text_callout import TextCalloutScene  # noqa: F401
from .brand_frame import BrandFrameScene  # noqa: F401
from .outro_cta import OutroCtaScene  # noqa: F401

SCENE_REGISTRY = {
    "equation": EquationScene,
    "code": CodeScene,
    "table": TableScene,
    "matrix": MatrixScene,
    "chart": {"bar": ChartBarScene, "line": ChartLineScene, "pie": ChartPieScene},
    "diagram": DiagramScene,
    "text_callout": TextCalloutScene,
    "brand_frame": BrandFrameScene,
    "outro_cta": OutroCtaScene,
}
