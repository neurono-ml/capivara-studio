# SEO Playbook

Metadados por plataforma. Sempre: keyword no início do título, CTA estratificado,
hashtags de nicho (não genéricas em excesso). Saída em `output/<sid>/final/metadata.json`
+ arquivos `.txt` prontos para colar.

## YouTube (long)

**Título**
- ≤ 100 caracteres; keyword principal **no início**.
- Fórmula: `[keyword] + benefício específico + delimitador`.
  - Bom: "Rust: como cortar tempo de build em 70% (guia completo)"
  - Ruim: "vídeo sensacional sobre rust que você vai amar ᐆ㐀"
- Emoji no máximo 1; sem all-caps; número concreto quando verdadeiro.

**Description**
- Primeiras 2 linhas aparecem antes de "mostrar mais" — colocar gancho + keyword ali.
- Timestamps/capítulos no formato `00:00 Intro` (obrigatório primeiro `00:00`).
- Link do artigo-fonte; links relacionados; sem bloat.

**Tags/hashtags**
- 3–5 hashtags; primeira posição são as mais importantes.
- Misturar 1 ampla + nicho + marca própria.

**Thumbnails:** primeiros 3 s devem funcionar como miniatura (qa_probe extrai).
Textos ≤ 4 palavras, alto contraste.

## YouTube Shorts

- Título ≤ 60 chars com keyword + #Shorts.
- Descrição mínima, 2–3 hashtags.
- Loop amigável: fim conectando com início aumenta retenção/replay.

## Instagram Reels

- **Primeira linha da caption = hook textual** (antes de "mais").
- 3–5 hashtags de nicho; evitar #reels #viral genéricos em massa.
- CTA textual curto na primeira linha ("Assiste até o 10s").
- Legendas burn-in obrigatórias (muitos assistem sem som).

## TikTok

- Primeira linha da caption = hook; ≤ 150 chars visíveis.
- 3–5 hashtags de nicho; 1 trending aceitável se genuína.
- TikTok favorece loop: vídeo que reinicia bem performa; validar no QA.
- Legendas burn-in obrigatórias.

## Carrossel Instagram

- Slide 1: capa com hook grande (text_callout) — sem esconder em sombra.
- Slides 2+: uma ideia por slide; última = CTA + handle/QR.
- Caption: gancho + 3–5 hashtags + "Salva pra depois" como CTA.

## CTA estratificado (resumo operacional)

| Plataforma | Início | Meio | Fim |
|---|---|---|---|
| YouTube long | hook de atenção | inscrição | comentário + inscrição |
| Shorts | hook | — | like/compartilhamento |
| Reels | hook | — | salva/compartilha |
| TikTok | hook | — | salva/compartilha |
| Carrossel | capa/hook | — | salva + segue |

## Checklist

- [ ] keyword no título, título dentro do limite
- [ ] timestamps só para long
- [ ] 3–5 hashtags de nicho (curto/IG)
- [ ] primeira linha = hook (curto/IG)
- [ ] metadata.json coerente com `manifest.json`
- [ ] nenhuma promessa não cumprida no vídeo
