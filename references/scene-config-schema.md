# Scene Config Schema (Markdown-encapsulated JSON Schema)

Cada scene config é **um JSON por cena**, gerado pelo scene-director em
`output/<sid>/scenes/<seg-id>.json`. As cenas são classes Manim no pacote
`scripts/manim_skills/` que lêem o config (`Scene._load_config()`); nenhum conteúdo é
hardcoded.

## Objeto raiz

```jsonc
{
  "id": "seg-004",                    // required, único na sessão
  "scene_type": "equation",           // required: equation|code|table|matrix|chart|diagram|text_callout|outro_cta
  "output_format": "video",           // required: "video" | "png" (ig_carousel usa png)
  "resolution": [1920, 1080],         // required: [w, h] exatos da plataforma
  "duration": 25.0,                   // required: segundos (real do TTS após resync)
  "platform": "yt-long",              // required: yt-long|yt_shorts|ig_reels|tiktok|ig_carousel
  "brand": "/work/brand/brand.local.json", // required: caminho no container (volume read-only)
  "params": { ... }                   // required: campos por scene_type, abaixo
}
```

## `brand` (THEME)

Carregado de `brand.local.json` (ou `brand.example.json`). Campos acessíveis às cenas:

```jsonc
{
  "palette": { "bg": "#0B0F1A", "fg": "#F5F5F5", "accent": "#FFD166", "accent2": "#7B5EA7", "muted": "#8B93A7" },
  "fonts": { "sans": "Noto Sans", "mono": "Noto Sans Mono" },
  "mascot": { "path": "/work/brand/assets/capivara.png", "emoji": "🐾" },
  "handle": "@handle",
  "frame": { "progress_bar": true, "watermark": true, "chapter_label": true }
}
```

Cena resolve cor/posição via `THEME` — nunca valores inline.

## campos `params` por `scene_type`

### `equation`
```jsonc
{ "latex": "E = mc^2",                      // required, string LaTeX (amsmath)
  "write_duration": 2.0,                    // optional, seg na animação de escrita (default 2)
  "steps": [                                 // optional, transformações passo-a-passo
    { "latex": "E = 9.0 \\times 10^{16}\\ \\text{J}", "highlight": { "substring": "10^{16}", "color": "accent" } }
  ]
}
```

### `code`
```jsonc
{
  "code": "def main():\n    return 42",      // required
  "language": "python",                      // required (SyntaxHighlight)
  "mode": "typewriter",                      // optional: "typewriter" | "lines" (default lines)
  "highlight_lines": [2],                    // optional (0-based)
  "comment_popup": " Aqui está o bug",       // optional texto pop-up
  "theme_dark": true                         // optional (default true)
}
```

### `table`
```jsonc
{
  "headers": ["Caso", "Tempo"],              // required
  "rows": [["Sem cache", "48 s"], ["Com cache", "6 s"]], // required
  "highlight_cells": [[1,1]],                // optional [row, col] (0-based, sem header)
  "row_reveal_duration": 0.8                 // optional por linha
}
```

### `matrix`
```jsonc
{
  "latex_main": "\\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix}", // required
  "transform": { "latex": "\\begin{bmatrix} 1 & 0 \\\\ 3 & 1 \\end{bmatrix}", "kind": "translate" } // optional kind: translate|rotate|scale
}
```

### `chart`
```jsonc
{
  "kind": "bar",                             // required: bar|line|pie
  "labels": ["Sem cache", "Com cache"],      // required
  "values": [48, 6],                         // required
  "accent_bar": 1,                           // optional índice destacado
  "animate_count": true,                     // optional contagem animada (default true)
  "show_axis": true                          // optional (bar/line)
}
```

### `diagram`
```jsonc
{
  "nodes": [{ "id": "a", "label": "Cliente" }, { "id": "b", "label": "Cache" }],
  "edges": [["a","b"]],
  "layout": "lr",                            // optional: "tb" | "lr" (default lr)
  "draw_sequence": [["a","b"]],              // optional ordem em que arestas se desenham
  "highlight_nodes": ["b"]                   // optional
}
```

### `text_callout`
```jsonc
{
  "text": "Você está fazendo isso errado",   // required
  "position": "center",                      // optional: center|top|safe_bottom
  "highlight_words": ["errado"],             // optional
  "mascot": true,                            // optional mascote entra (default false)
  "mascot_side": "bottom_right"              // optional: bottom_right|bottom_left
}
```

### `outro_cta`
```jsonc
{
  "cta_text": "Salva pra depois",            // required
  "sub_cta": "comente o próximo tema",       // optional
  "handle": "@handle",                       // optional (sobrescreve brand.handle)
  "qr": "/work/brand/assets/qr.png",         // optional caminho do QR (host)
  "mascot": true                             // optional (default true)
}
```

## Constraints

- `duration` > 0 e ≤ duração total do formato.
- `resolution` deve bater exatamente com a plataforma (ver `platform-specs.md`).
- Campos texto não vazios; LaTeX compilável com TinyTeX minimal (amsmath/amssymb).
- `ig_carousel` → `output_format: "png"` (PNGs 1080x1350, um config por slide).
- Nenhum caminho do host; apenas caminhos `/work/...` (dentro do container).
