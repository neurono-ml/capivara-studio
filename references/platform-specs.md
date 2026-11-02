# Platform Specs

Tabela de plataformas, resoluções, durações e restrições.

| Plataforma | `format` | Resolução | Aspecto | Duração | Container/Codec | Saída |
|---|---|---|---|---|---|---|
| YouTube longo | `yt-long` | 1920x1080 | 16:9 | 10–20 min (600–1200 s) | MP4 / H.264, AAC 192k | video |
| YouTube Shorts | `yt_shorts` | 1080x1920 | 9:16 | 10–60 s (≤ 60 s para contar como Short) | MP4 / H.264, AAC 192k | video |
| Instagram Reels | `ig_reels` | 1080x1920 | 9:16 | 15–60 s | MP4 / H.264, AAC 192k | video |
| TikTok | `tiktok` | 1080x1920 | 9:16 | 10–60 s | MP4 / H.264, AAC 192k | video |
| Carrossel Instagram | `ig_carousel` | 1080x1350 | 4:5 | — | PNG | imagem |

Todos os vídeos finais: `-c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart`,
áudio AAC 192k, loudness alvo ~ -14 LUFS.

## Normalização de resolução (assembler)

- Fonte 1920x1080 → `yt-long`: uso direto.
- Fonte 1920x1080 → verticais: `scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2` (fundo cor do tema).
- Fonte vertical → verticais: uso direto.
- Fonte vertical → `yt-long`: `scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2`.
- Nunca esticar; sempre scale (mantém proporção) + pad (letterbox com cor da marca).
- Crop alternativo (quando a composição permitir): `crop` central para cobrir o frame.

## Safe zones (9:16, 1080x1920)

A UI corta/obre parte do frame vertical. Manter **todo texto, mascote, CTA e elementos
críticos dentro da safe-area**:

| Zona | px (em 1080x1920) | Conteúdo |
|---|---|---|
| Topo cortado | ~0–200 | Riskeado: legendas de UI, username overlay, "Para você" |
| Base cortada | ~1670–1920 | Riskeado: caption, botões curtir/compartilhar, barra de progresso |
| Safe-area útil | **y: 200–1670** | Todo conteúdo desenhado aqui |

Orientações:
- Hook e CTA sempre em `y >= 250` e `y <= 1620`.
- Legendas burn-in: base em `y ≈ 1450–1600` (acima da zona de caption do TikTok, mas
  dentro da área visível).
- Margem lateral: manter ≥ 60 px das bordas esquerda/direita.
- Em 1080x1350 (carrossel 4:5) não há overlay agressivo, mas manter margem ≥ 60 px.

## Duração por formato (alvo do script-writer)

| Formato | Total | Nota |
|---|---|---|
| `yt-long` | 600–1200 s | Cold-open 7 s + "o que vai aprender" + capítulos |
| `yt_shorts` | 10–60 s | Hook < 2 s |
| `ig_reels` | 15–60 s | Hook < 2 s, ritmo rápido |
| `tiktok` | 10–60 s | Hook < 2 s, loop amigável (fim conecta ao início) |
| `ig_carousel` | 4–10 slides | Slide 1 = capa/hook |

## Thumbnails

- YouTube longo: frame representativo dos primeiros 3 s (`qa_probe.sh` extrai) — o hook
  visual deve ser forte o suficiente para servir de miniatura.
- Shorts/Reels/TikTok: os primeiros 3 s também, pois a preview mostra o início.
