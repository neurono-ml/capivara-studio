"""diagram_scene.py — grafo/flowchart com arestas desenhando-se em sequência.

params:
  nodes (list[{id, label}], obrigatório)
  edges (list[[id_a, id_b]], obrigatório)
  layout ("tb" | "lr", default "lr")
  draw_sequence (list[[id_a, id_b]], opt — ordem customizada)
  highlight_nodes (list[id], opt)
"""
from manim import (
    RoundedRectangle, VGroup, Create, Text, Arrow, RIGHT, LEFT, UP, DOWN,
)
from manim import config as manim_config

from .config_loader import ConfigScene


class DiagramScene(ConfigScene):
    """Cena de diagrama parametrizada (grafo/flowchart)."""

    def construct(self):
        cfg = self._load_config()
        params = cfg.get("params", {}) or {}
        nodes_def = params.get("nodes") or []
        edges_def = params.get("edges") or []
        draw_seq = params.get("draw_sequence") or edges_def
        layout = (params.get("layout") or "lr").lower()
        highlights = params.get("highlight_nodes") or []

        if not nodes_def:
            nodes_def = [{"id": "n1", "label": "?"}]

        # --- layout: pilares por camada em grafo DAG simplificado (ordem de inserção)
        positions = self._layout_positions(nodes_def, edges_def, layout)

        node_mobjs = {}
        node_group = VGroup()
        for node in nodes_def:
            nid = node.get("id")
            label = str(node.get("label", nid))
            cx, cy = positions[nid]
            chip = RoundedRectangle(
                corner_radius=0.12,
                width=max(len(label) * 0.16 + 0.4, 1.0),
                height=0.72,
                fill_color=(self.accent2 if nid in highlights
                            else self.THEME["palette"]["bg"]),
                fill_opacity=0.35 if nid in highlights else 0.96,
                stroke_color=self.muted,
                stroke_width=1.0,
            )
            chip.move_to([cx, cy, 0])
            text = Text(label, font=self.font_sans, font_size=22,
                        color=self.fg).move_to(chip)
            node_mobjs[nid] = VGroup(chip, text)
            node_group.add(node_mobjs[nid])

        # --- nós entram primeiro (em ordem de inserção)
        per_node = max((self.DURATION * 0.35) / max(len(nodes_def), 1), 0.2)
        for node in nodes_def:
            self.play_timed(Create(node_mobjs[node["id"]]), run_time=per_node)

        # --- arestas desenhando em sequência com setas
        per_edge = max((self.DURATION - self._elapsed - 0.6) / max(len(draw_seq), 1), 0.3)
        for (a, b) in draw_seq:
            if a not in node_mobjs or b not in node_mobjs:
                continue
            from manim import Arrow
            arrow = Arrow(
                start=node_mobjs[a].get_edge_center(RIGHT if layout == "lr" else DOWN),
                end=node_mobjs[b].get_edge_center(LEFT if layout == "lr" else UP),
                color=self.muted, buff=0.12, stroke_width=2.2,
                max_tip_length_to_length_ratio=0.25,
            )
            self.play_timed(Create(arrow), run_time=per_edge)

        self.finish_scene()

    # ------------------------------------------------------------- layout
    def _layout_positions(self, nodes_def, edges_def, layout):
        """Posições por camada (topo→baixo em tb; esquerda→direita em lr),
        dentro da safe-area vertical."""
        h = manim_config.frame_height
        safe_top = -h / 2 + (self.SAFE_TOP_PX / manim_config.pixel_height) * h + 0.5
        safe_bottom = h / 2 - (self.SAFE_BOTTOM_PX / manim_config.pixel_height) * h - 0.5
        span_y = safe_top - safe_bottom

        # concentra o cálculo: BFS por camadas a partir de nós sem aresta de entrada
        indegree = {n["id"]: 0 for n in nodes_def}
        adjacency = {}
        for (a, b) in edges_def:
            if a in indegree and b in indegree:
                adjacency.setdefault(a, []).append(b)
                indegree[b] += 1
        layer = {}
        frontier = [nid for nid, d in indegree.items() if d == 0]
        depth = 0
        seen = set()
        while frontier:
            nxt = []
            for nid in frontier:
                if nid in seen:
                    continue
                seen.add(nid)
                layer[nid] = depth
                for adj in adjacency.get(nid, []):
                    nxt.append(adj)
            depth += 1
            frontier = nxt
        # nós desconectados/ciclos entram na primeira camada disponível
        max_depth = max([depth, 1])
        for n in nodes_def:
            if n["id"] not in layer:
                layer[n["id"]] = 0
        laid = max(layer.values()) + 1

        #Profundidade: eixo principal; posição lateral: distribui entre os nós da camada
        positions = {}
        per_depth = span_y / max(laid, 1)
        for n in nodes_def:
            nid = n["id"]
            same_layer = [other["id"] for other in nodes_def
                          if layer[other["id"]] == layer[nid]]
            idx = same_layer.index(nid) if nid in same_layer else 0
            lateral = (idx - (len(same_layer) - 1) / 2) * 2.0
            if layout == "lr":
                x = -manim_config.frame_width / 2 + 0.8 + \
                    (layer[nid] / max(laid - 1, 1)) * (manim_config.frame_width - 1.6)
                y = lateral
            else:
                y = safe_bottom + per_depth * (laid - 1 - layer[nid] + 0.5)
                x = lateral
            positions[nid] = (x, y)
        return positions
