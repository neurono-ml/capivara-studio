"""registry — resolve a classe Manim apropriada por scene_type (+kind do chart)."""
from typing import Type

from manim import Scene

from .equation import EquationScene
from .code_scene import CodeScene
from .table_scene import TableScene
from .matrix_scene import MatrixScene
from .chart_scene import ChartBarScene, ChartLineScene, ChartPieScene
from .diagram_scene import DiagramScene
from .text_callout import TextCalloutScene
from .brand_frame import BrandFrameScene
from .outro_cta import OutroCtaScene

_SCENE_BY_TYPE = {
    "equation": EquationScene,
    "code": CodeScene,
    "table": TableScene,
    "matrix": MatrixScene,
    "diagram": DiagramScene,
    "text_callout": TextCalloutScene,
    "brand_frame": BrandFrameScene,
    "outro_cta": OutroCtaScene,
}

_CHART_BY_KIND = {
    "bar": ChartBarScene,
    "line": ChartLineScene,
    "pie": ChartPieScene,
}


def get_scene_class(scene_type: str, chart_kind: str = "") -> Type[Scene]:
    """Retorna a classe de cena apropriada. Lança KeyError para tipo desconhecido."""
    if scene_type == "chart":
        return _CHART_BY_KIND[chart_kind]
    return _SCENE_BY_TYPE[scene_type]
