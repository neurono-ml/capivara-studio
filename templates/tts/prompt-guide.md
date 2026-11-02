# TTS Prompt Guide (voice-director)

O TTS é **externo**: provider escolhido pelo usuário no ambiente local
(`env TTS_PROVIDER`, chave em `TTS_API_KEY`). Nada de chave, endpoint ou prompt
pessoal vai para config, roteiro ou imagem. Esta skill **não** embute SDKs: baixar
um arquivo por segmento via HTTP com a chave no header do lado do host.

## Providers suportados (padrões compatíveis)

| Provider | Endpoint (padrão) | Voz | Parâmetros úteis |
|---|---|---|---|
| `openai` | `POST {OPENAI_BASE}/v1/audio/speech` | `model=gpt-4o-mini-tts`, `voice=alloy…`, `speed=0.8–1.2` | `response_format=mp3` |
| `elevenlabs` | `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}` | `voice_settings.stability`, `similarity_boost` | `xi-api-key` header |
| genérico | `TTS_URL` + `TTS_API_KEY` | conforme API | qualquer compatível |

## Prompt/parâmetros recomendados

- **Velocidade:** `speed=1.0` base. Para TikTok/Reels testar `1.05–1.10` (ritmo).
- **Pausa:** controlar pela pontuação do texto — `…` pausa média, `.` pausa cheia,
  `—` pausa curta de respiro. Ajuste fino: quebrar narracao em 1 frase por linha e
  colocar `\n` (OpenAI tts-1/gpt-4o-mini-tts e ElevenLabs respeitam).
- **Tom:** for `openai`, usar campo `instructions` com 1 frase do estilo do autor
  (pegue de `brand.local.json → voice.tone_examples`, no host).
  Ex.: "Fala direta, técnica, com humor leve. Nada dramático."
- **Formato:** `mp3 48k mono` para `concat_audio_video.sh`.

## Ciclo do voice-director (por segmento)

1. Ler `script.json` → `narracao` do segmento (reescreve nada; quem escreveu foi o
   script-writer na voz certa).
2. Montar payload provider (modelo, voice_id, speed, instructions).
3. `curl -f -H "Authorization: Bearer ${TTS_API_KEY}" ... -o output/<sid>/audio/<seg-id>.mp3`
4. Medir duração real:
   ```bash
   scripts/docker-run.sh ffprobe -v error -show_entries format=duration \
     -of csv=p=0 /work/output/<sid>/audio/<seg-id>.mp3
   ```
5. **Resync:** atualizar `duration` no config de cada cena
   (`output/<sid>/scenes/<seg-id>.json`) = duração real do áudio ±0,3s. Escrever
   também `real_duration` em `manifest.json`.
6. Se diferença entre duração real e `duracao_alvo_s` > 15%: re-render é exigível
   (pode recorrer ao scene-director).

## Integração com manifest.json

```jsonc
{
  "scenes": [
    {
      "id": "seg-003",
      "status": "success",
      "video_path": "output/abc/seg-003.mp4",     // do results.json
      "audio_path": "output/abc/audio/seg-003.mp3", // do voice-director
      "duration": 25.4,     // real, pelo ffprobe
      "config_sha256": "..."  // do render_manim.py, para idempotência
    }
  ]
}
```

`concat_audio_video.sh` consome exatamente estas chaves. Sem `audio_path`, o
assembler monta com silêncio naquele segmento (permitido: cena sem voz).

## Checklist

- [ ] Chave nunca em config/log (usar env; `-H` no shell com `${TTS_API_KEY}`)
- [ ] Duração medida por ffprobe, não estimada
- [ ] mp3 48k mono; AAC 192k só no assembler
- [ ] `manifest.json` atualizado antes do assembler
