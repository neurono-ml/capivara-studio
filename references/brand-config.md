# Brand Config

**Regra de ouro: NENHUM conteúdo pessoal entra na imagem Docker.** A imagem é pública e
open-source (GHCR). Paleta, mascote, handle, QR e prompts vivem **no host** e são
montados por volume read-only.

## Arquivos

| Arquivo | Onde | Existe em git? |
|---|---|---|
| `brand.local.json` | host, junto de `output/` | ❌ gitignored |
| `brand.example.json` | `agents/skills/capivara-studio/templates/` | ✅ genérico |

## Esquema (brand.local.json)

```jsonc
{
  "palette": {
    "bg": "#000000",     // fundo
    "fg": "#FFFFFF",     // texto principal
    "accent": "#FFD166", // cor de ação (highlight, barras)
    "accent2": "#7B5EA7", // cor secundária
    "muted": "#8B93A7"   // texto secundário
  },
  "fonts": { "sans": "Noto Sans", "mono": "Noto Sans Mono" },
  "mascot": {
    "path": "/work/brand/assets/capivara.png", // PNG com canal alpha
    "emoji": "🐾"                               // fallback textual
  },
  "handle": "@seuhandle",
  "frame": {
    "progress_bar": true,   // faixa de progresso no topo
    "watermark": true,      // watermark discreto
    "chapter_label": true   // rótulo do capítulo atual
  },
  "voice": {
    "tone_examples": ["frases que representam seu estilo"],
    "tts_voice_id": ""      // aponta para provider externo; chave nunca aqui
  }
}
```

## Montagem no container

`scripts/docker-run.sh` monta a pasta do host para `/work/brand/` (read-only):
config + `assets/` (mascote PNG, QR, molduras por plataforma se houver).
As cenas leem `THEME` desse JSON. Sem `brand.local.json`, usar `templates/brand.example.json`.

## Fallback quando brand ausente

Usar `brand.example.json` (fundo escuro genérico, accent amarelo/roxo, mascote ausente →
cenas usam só o emoji textual). Nunca criar cores próprias hardcoded em cena.
