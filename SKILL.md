---
name: capivara-studio
description: "Gera vídeos longos de YouTube (16:9 1080p H.264), YouTube Shorts, Instagram Reels e TikTok (9:16) e carrosséis Instagram (4:5) a partir de artigos: roteiro com SEO por plataforma, cenas Manim animadas (equações, código, gráficos, tabelas, diagramas), TTS com dublagem, montagem FFmpeg e pipeline Docker reprodutível — pipeline completo artigo→vídeo."
version: 0.1.0
author: neurono-ml
license: MIT
---

# capivara-studio

Skill de produção de vídeo programático para OpenCode. Gera três formatos:

| Formato | Resolução | Aspecto | Duração | Saída |
|---|---|---|---|---|
| YouTube longo | 1920x1080 | 16:9 | 10–20 min | MP4/H.264 |
| Shorts / Reels / TikTok | 1080x1920 | 9:16 | 10–60 s | MP4/H.264 |
| Carrossel Instagram | 1080x1350 | 4:5 | — | PNG |

Toda a renderização roda **dentro de Docker** (imagem `ghcr.io/neurono-ml/capivara-studio-runner:latest`,
base `debian:12-slim` com Manim 0.18.1 + FFmpeg + TinyTeX). Nada pessoal entra na imagem:
paleta, mascote (Capivara) e prompts ficam no host em `brand.local.json` (gitignored) e são
montados por volume.

## Estrutura

```
.agents/skills/capivara-studio/
├── SKILL.md                ← este arquivo (orquestração)
├── README.md               ← instalação e uso
├── references/             ← specs, guias de estilo, SEO, schema de cena, brand config
├── scripts/                ← shell + CLI Python (docker-run.sh, render_manim.py, concat/qa/validate)
│   └── manim_skills/       ← pacote de cenas Manim parametrizadas
├── templates/              ← configs por formato + guia TTS
└── docker/                 ← Dockerfile, requirements.txt, build.sh, smoke-test.sh
```

## Fluxo de orquestração (8 etapas)

Fluxo: **1 → 2 → 3 → (4 ∥ 5) → 6 → 7 → 8**. Output idempotente por sessão em
`output/<session-id>/` com `manifest.json`.

Todas as saídas da sessão vivem em `output/<session-id>/`:

```
output/<session-id>/
├── manifest.json      ← cenas, hashes, caminhos, durações, status
├── script/            ← roteiro segmentado (script.json + narracao por segmento)
├── scenes/            ← configs JSON por cena + MP4/PNG renderizados
├── audio/             ← TTS por segmento
└── final/             ← vídeo final + metadados SEO + thumbnail
```

Regra de idempotência: antes de renderizar, conferir hash do config em `manifest.json`;
se igual e o output existe e passa, pular a cena (permite retomar sessão interrompida).

---

### Etapa 1 — content-researcher

Subagente único, sequencial.

**Entrada:** tema OU artigo-fonte (caminho local, URL ou texto colado).

**Instruções operativas para o OpenCode:**
1. Se não houver artigo: pesquisar no tema (websearch se disponível), levantar dados,
   estatísticas, exemplos e contraexemplos. Identificar 3–5 pontos que "rendem cena Manim"
   (equação, gráfico, tabela, diagrama de código).
2. Se houver artigo: extrair estrutura, claims verificáveis, dados quantificáveis e o
   "valor prático" para o espectador.
3. Carregar estilo do autor de `references/script-style-guide.md` + `brand.local.json`
   (se existir no host, via volume montado em `/work/brand/`).
4. Se o artigo precisar ser gerado/enriquecido primeiro, escrevê-lo em
   `output/<session-id>/script/artigo-fonte.md` antes de prosseguir.

**Saída:** dossiê de conteúdo (markdown) com claims, dados e candidatos a visual.

### Etapa 2 — script-writer

Subagente único, sequencial.

**Entrada:** dossiê da etapa 1 + formato alvo (`yt-long` | `yt_shorts` | `ig_reels` |
`tiktok` | `ig_carousel`).

**Contrato JSON do roteiro** — escrever em `output/<session-id>/script/script.json`:

```json
{
  "session_id": "abc123",
  "format": "yt-long",
  "target_duration_s": 720,
  "total_duration_s": 718,
  "brand": "brand.local.json",
  "segments": [
    {
      "id": "seg-001",
      "chapter": "Intro",
      "cta": null,
      "tipo_de_cena": "text_callout",
      "narracao": "Exatamente o texto que o TTS vai ler. Frases faladas, não literais.",
      "duracao_alvo_s": 7,
      "elementos_visuais": "hook 'Você está fazendo isso errado' + mascote entrando"
    },
    {
      "id": "seg-002",
      "chapter": "Diagnóstico",
      "cta": "subscribe_mid",
      "tipo_de_cena": "equation",
      "narracao": "...",
      "duracao_alvo_s": 25,
      "elementos_visuais": "equação passo a passo com highlight no termo errado"
    }
  ]
}
```

**Validação obrigatória antes de prosseguir:**
- Σ `duracao_alvo_s` == `target_duration_s` (±5 s). Se bater fora, reescrever segmentos,
  não omitir a checagem.
- Vídeo longo: cold-open nos primeiros 7 s; logo depois "o que você vai aprender";
  capítulos; open loops recorrentes ("volta no capítulo 3"); **CTA de inscrição no MEIO,
  não apenas no fim**; CTA final de comentário/inscrição.
- Shorts/Reels/TikTok: hook < 2 s; CTA de like/compartilhamento no fim; narração calibrada
  para duração real do TTS (ver etapa 5 e `templates/tts/prompt-guide.md`).
- Amaarrar o roteiro: nada pessoal/secreto no roteiro; mascote e paleta são referência,
  não texto.

Tipos de cena válidos (ver `references/scene-config-schema.md`): `equation`, `code`,
`table`, `matrix`, `chart`, `diagram`, `text_callout`, `brand_frame` (injetada
automaticamente), `outro_cta`.

### Etapa 3 — scene-director

Subagente único, sequencial.

**Tarefa:** para cada segmento, produzir um **config JSON de cena** (não código de cena!)
conforme `references/scene-config-schema.md`, em
`output/<session-id>/scenes/<seg-id>.json`.

- Todo config **carrega THEME do brand-config local**: cada cena tem um campo `brand`
  apontando para o JSON de marca (cores, fontes, dimensões por plataforma, caminho/emoji do
  mascote). Nunca embutir cores pessoais no config gerado.
- Escolher tipo de cena mais expressivo por segmento; cenários com número/dado → `chart`/`table`;
  lógica/matematica → `equation`/`matrix`; código → `code`; conceito/estrutura → `diagram`;
  hook/transição/CTA → `text_callout`/`outro_cta`.
- `duracao` da cena = `duracao_alvo_s` do segmento (será refinada na etapa 5).
- Ler specs de safe-zone de `references/platform-specs.md`: em 1080x1920, texto e CTA
  fora das zonas cortadas pela UI (topo ~200px, base ~250px).
- Escrever/atualizar `output/<session-id>/manifest.json` já listando os configs.

### Etapa 4 — scene-render-worker (PARALELO)

**N subagentes em paralelo.** Divida a lista de configs em lotes balanceados por
`duracao` estimada (ex.: 2–4 cenas por worker). Cada worker:

1. Chama `scripts/docker-run.sh render_manim.py --scenes /work/output/<session-id>/scenes/...` (pode
   passar um único JSON ou o diretório inteiro; o worker pode rodar com `--filter seg-00X`
   quando implementado, senão lotes = subconjunto de arquivos passados um a um).
2. **Sem lógica, só execução.** Se uma cena falha, registrar a falha + log e **seguir o lote**
   (uma cena não aborta o worker). Retentar a cena falha até 2× antes de marcar `failed`.

Faixa paralela: rodar workers em paralelo **e** a etapa 5 em paralelo com a 4
(`4 ∥ 5`), pois TTS independe de render. Só a etapa 6 depende das duas.

### Etapa 5 — voice-director

**Executar em paralelo com a etapa 4.**

1. Ler `templates/tts/prompt-guide.md`. Chamar o provider TTS EXTERNO configurado pelo
   usuário (OpenAI / ElevenLabs compatível) — a chave fica no ambiente local
   (env `TTS_API_KEY` / `TTS_PROVIDER`), **nunca embutida em config, prompt ou imagem**.
2. Um arquivo de áudio por segmento: `output/<session-id>/audio/<seg-id>.mp3` (ou .wav).
3. Medir duração real de cada segmento com `scripts/docker-run.sh ffprobe -v error -show_entries format=duration -of csv=p=0 <arquivo>`.
4. **Resync:** repassar o timing real ao scene-director (eu mesmo, na mesma conversa):
   atualizar campo `duracao` de cada config de cena = duração real do áudio ±0,3 s e
   reescrever o JSON (a re-renderização da cena, se já renderizada, só é necessária se a
   diferença > 15%; senão, pós-ajuste na montagem).
5. Atualizar `manifest.json` com caminhos de áudio e durações reais.

### Etapa 6 — assembler

Subagente único, sequencial. Depois de 4 e 5 concluídas:

1. Rodar `scripts/concat_audio_video.sh` via `docker-run.sh`:
   - concatenar cenas com crossfade 0.3 s (xfade / xfade de áudio);
   - muxar narração TTS nas posições de cada segmento (adelay + amix);
   - música de fundo opcional (parâmetro `--music <arquivo>` — arquivo fornecido no host,
     NUNCA embutido);
   - normalizar para a plataforma (scale/pad/crop conforme `references/platform-specs.md`);
   - **codec: `-c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart`; áudio AAC 192k;
     alvo ~ -14 LUFS** (`loudnorm`).
2. Saída: `output/<session-id>/final/video-final.mp4`.
3. Carrossel: usar `render_manim.py` com configs `ig_carousel` → PNGs 1080x1350, empacotar
   em `final/carousel/`.

### Etapa 7 — seo-publisher

Subagente único, sequencial. Ler `references/seo-playbook.md` e gerar
`output/<session-id>/final/metadata.json` + arquivos de texto por plataforma:

- **YouTube longo:** título ≤ 100 chars com keyword no início; description com resumo,
  timestamps/capítulos (formato `00:00`), links; hashtags nas primeiras posições.
- **Shorts:** título curto com keyword; #Shorts.
- **Reels/TikTok:** caption com hashtags de nicho (3–5, nenhuma genérica exagerada), hook
  textual na primeira linha.
- **Carrossel IG:** caption + primeira imagem já contextualizada (hook no slide 1).
- CTA estratificado: hook no início, inscrição no meio (já no roteiro), comentário no fim.
- Nada de promessas falsas / clickbait sem entrega.

### Etapa 8 — qa-reviewer

Subagente único, sequencial. Rodar `scripts/qa_probe.sh` via `docker-run.sh`:

- codec == h264; resolução exata da plataforma (tabela em `references/platform-specs.md`);
- duração dentro da faixa (Shorts ≥ 10 s para contar como Short; ≤ 60 s para TikTok/Reels);
- thumbnail dos primeiros 3 s (`qa_probe.sh` extrai e salva em `final/thumbnail.jpg`);
- áudio presente e com loudness normalizado;
- legendas obrigatórias para TikTok/Reels (burn-in) — se faltar, voltar ao assembler com
  flag `--subtitles-burn-in` e arquivo de legendas gerado do roteiro.

**Loop de correção:** QA pode falhar. Execute até 2 ciclos completos de correção
(assembler → qa) antes de reportar falha definitiva. Se uma única cena foi a causa,
re-render só essa cena (idempotência por hash).

---

## Contratos rápidos

**Cena (resumo)** — ver `references/scene-config-schema.md` para o JSON Schema completo:

```json
{
  "id": "seg-004",
  "scene_type": "equation",
  "output_format": "video",
  "resolution": [1920, 1080],
  "duration": 25.0,
  "brand": "/work/brand/brand.local.json",
  "platform": "yt-long",
  "params": {
    "latex": "E = mc^2",
    "steps": ["destacar 'E'", "substituir por número"],
    "accent": "#FFD166"
  }
}
```

**Comandos principais** (todos os caminhos relativos à raiz da skill):

```bash
# validar ambiente
scripts/validate_env.sh

# render de cenas (passa config dir por volume read-only)
scripts/docker-run.sh python /work/scripts/render_manim.py --scenes /work/output/<sid>/scenes

# montagem final
scripts/docker-run.sh bash /work/scripts/concat_audio_video.sh --in /work/output/<sid> --platform yt-long

# QA
scripts/docker-run.sh bash /work/scripts/qa_probe.sh /work/output/<sid>/final/video-final.mp4 --platform yt-long
```

**Subagentes em paralelo — quando:**
- Etapas 4 e 5 sempre em paralelo (grupo `4 ∥ 5`).
- Etapa 4: N workers em paralelo, lotes por duração; cada worker itera seus configs.
- Nunca paralelizar 1, 2, 3, 6, 7, 8 entre si.

**Idempotência:** `manifest.json` é fonte da verdade. Hash SHA-256 de cada config +
`status` + caminho de output. Reexecução pula o que já passou.

**Segurança:** nada pessoal, nenhum secret, nenhum caminho do host entra em config,
código de cena ou imagem. `brand.local.json` fica no host e é montado read-only.
