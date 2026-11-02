# Script Style Guide

## Princípio central: escrever para VOZ

O roteiro é lido por um TTS. Texto literário soa robótico. Regras:

1. Frases curtas, de fala. Se você não diria isso em voz alta numa conversa, reescreva.
2. Nenhuma lista longa de substantivos; prefira verbos ("filtrar os logs" e não
   "efetuação de filtragem de logs").
3. Números "por extenso em texto corrido" quando TTS confunde; ou formate para leitura
   ("mil e duzentos" vs "1.200" — testar no provider).
4. Abreviações faladas: "API" fica "API" (o TTS lê por letra); "e.g." não — troca por
   "por exemplo".
5. Pausa: usar pontuação para controlar TTS (`. , … — ?`); prompt provider veja
   `templates/tts/prompt-guide.md`.

## Duração do texto ≈ duração do áudio

Português falado: ~ **2.7–3.2 palavras/segundo** (TTS nessa faixa).

- Segmento de 20 s ≈ 55–64 palavras.
- Valide mentalmente: se `narracao` de um segmento de 5 s tem 50 palavras, ou o TTS vai
  acelerar demais (ma qualidade), ou o segmento estoura. Reescrever.

## Cold open (vídeos longos)

- Primeiros ~7 s: afirmação direta, dado surpreendente ou pergunta que dói.
  Proibido começar com "Olá pessoal, bem-vindo ao canal".
- Após o cold open: slide/texto "o que você vai aprender" com 3 bullets em <= 15 s.
- Depois: capítulos nomeados; entre capítulos, 1 frase de transição com open loop
  ("e é aqui que entra a parte que ninguém te conta — no capítulo 3").

## Open loops

- Anuncie no início o que será resolvido no fim; cumpra no fim.
- Recorrer a 2–3 mini-cliffhangers entre capítulos.
- Nunca abra mais loops do que fecha.

## CTA por plataforma

| Posição | Vídeo longo | Shorts/Reels/TikTok |
|---|---|---|
| Início | Cold open já é o "CTA de atenção" | Hook < 2 s |
| Meio | **CTA de inscrição** ("se isso te ajudou até aqui, inscreve — o melhor ainda vem") | — |
| Fim | CTA de comentário ("comente qual tópico pro próximo vídeo") + inscrição | CTA de like/compartilhamento ("manda pra quem precisa disso") |

- 1 CTA por posição, sem repetição exaustiva.
- CTA é fala, não texto de pastoral ("consideramos-lhe convidar" ❌).

## Hook (Shorts/Reels/TikTok)

- < 2 s = ~5–7 palavras.
- Padrões eficazes: negação ("você está fazendo X errado"), número específico,
  contraste ("30 minutos → 3 segundos"), segredo ("a doc não te mostra isso").
- O visual do hook (`tipo_de_cena: text_callout`) deve casar com a fala.

## Tom e estilo do autor

- Carregar preferências de `brand.local.json` (campo `voice.tone_examples`) quando
  existir; fallback: direto, técnico-acessível, humor leve, sem formalidades excessivas.
- Proibido: jargão sem explicação, promessas irreais, clickbait sem entrega.
- "Engralesado" para IG/TikTok: cores vivas do tema, ritmo de corte rápido (cenas
  curtas 3–6 s), mascote Capivara presente no hook e no CTA.

## Checklist de saída do script-writer

- [ ] Σ durações == alvo (±5 s)
- [ ] cold-open (long) / hook < 2 s (curto)
- [ ] capítulos nomeados + (long) timestamps possíveis
- [ ] open loop anunciada e fechada
- [ ] CTA de inscrição no meio (long) / fim (curto)
- [ ] CTA final
- [ ] narração em frases de fala
- [ ] nada pessoal ou secreto no texto
