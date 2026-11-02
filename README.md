# capivara-studio

Skill para o OpenCode que gera vídeos e carrosséis a partir de artigos — **pipeline completo artigo→vídeo** (roteiro com SEO por plataforma, cenas Manim animadas, TTS com dublagem, montagem FFmpeg H.264, tudo em Docker reprodutível):

| Formato | Resolução | Aspecto | Duração | Saída |
|---|---|---|---|---|
| YouTube longo | 1920x1080 | 16:9 | 10–20 min | MP4/H.264 |
| YouTube Shorts / Instagram Reels / TikTok | 1080x1920 | 9:16 | 10–60 s | MP4/H.264 |
| Carrossel Instagram | 1080x1350 | 4:5 | — | PNG |

Pipeline: roteiro segmentado → cenas **Manim** parametrizadas → TTS externo →
montagem FFmpeg com crossfade/H.264/AAC — tudo dentro de Docker
(`debian:12-slim` + Manim 0.18.1 + FFmpeg + TinyTeX).

**Público/open-source:** nada pessoal entra na imagem. Paleta, mascote (Capivara),
handle/QR e prompt de estilo ficam no host em `brand.local.json` (gitignored) e
são montados por volume **read-only**.

## Pré-requisito

Só **Docker** (ou Podman). Não precisa Python/Manim localmente.

## Instalação

Após publicar como repo separado (`neurono-ml/capivara-studio`), instalar
via agent-skills:

```bash
npx skills add neurono-ml/capivara-studio
```

Alternativa: clonar este repo e apontar a skill em `~/.agents/skills/`:

```bash
git clone https://github.com/neurono-ml/capivara-studio.git \
  ~/.agents/skills/capivara-studio
# (se vier como subpasta do repo opencode-voice-plugin:
#  cp -r .agents/skills/capivara-studio ~/.agents/skills/)
```

## Uso no OpenCode

```
use a skill capivara-studio para criar:
  - YouTube 15 min a partir de <artigo> (formato yt-long)
  - um Short 45s sobre <tema> (formato yt_shorts)
  - Reels 35s versão vertical de <tema> (formato ig_reels)
  - TikTok 30s (formato tiktok)
  - carrossel IG com 8 slides de <artigo> (formato ig_carousel)
```

## Primeiro uso

1. `docker/build.sh` — builda a imagem local (ou aguarde o push do GHCR).
2. `scripts/validate_env.sh` — checks de ambiente (runtime, imagem, brand, TTS key).
3. Crie optional `brand/brand.local.json` + `brand/assets/` (mascote PNG com alpha, QR).
   Sem isso, a skill usa `templates/brand.example.json` genérico.
4. Defina no ambiente: `TTS_PROVIDER`, `TTS_API_KEY` (ver `templates/tts/prompt-guide.md`).
5. No OpenCode, a SKILL.md orquestra as 8 etapas com subagentes.

## Pipeline (o que cada etapa faz)

1. **content-researcher** — dossiê de artigo/dados.
2. **script-writer** — `script.json` (segmentos: narração, tipo de cena, duração; validação Σ = alvo).
3. **scene-director** — `scenes/<id>.json` por cena (moldes no schema, THEME do brand).
4. **scene-render-worker** (N paralelos) ∥ 5. **voice-director** — TTS + sync.
6. **assembler** — `concat_audio_video.sh` (xfade 0.3, narration mux, loudnorm −14 LUFS, faststart).
7. **seo-publisher** — títulos/hashtags/timestamps por plataforma.
8. **qa-reviewer** — `qa_probe.sh` (codec, resolução exata, duração, thumbnail, áudio).

Output idempotente por sessão: `output/<session-id>/` + `manifest.json`
(cenas, hash SHA-256 de cada config, caminhos, durações, status).

## Estrutura

```
.agents/skills/capivara-studio/
├── SKILL.md            # orquestração (instruções operativas)
├── README.md
├── references/         # platform-specs, style guide, SEO, schema de cena, brand
├── scripts/            # docker-run.sh, render_manim.py, concat_audio_video.sh, qa_probe.sh, validate_env.sh
│   └── manim_skills/   # cenas Manim: equation, code, table, matrix, chart, diagram, text_callout, brand_frame, outro_cta
├── templates/          # configs de exemplo por formato + guia TTS
└── docker/             # Dockerfile, requirements.txt, build.sh, smoke-test.sh
```

## CI

- `.github/workflows/docker-publish.yml` — multi-arch (amd64+arm64), Trivy
  (HIGH/CRITICAL fail), push no GHCR (latest, vX.Y.Z, sha-short) com cache GHA.
- `.github/workflows/smoke-test.yml` — PRs rodam smoke-test sem push.

Licença MIT. Conteúdo gerado é seu.
