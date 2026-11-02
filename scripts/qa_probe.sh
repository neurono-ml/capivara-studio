#!/usr/bin/env bash
# qa_probe.sh — validação técnica do output final (rodar DENTRO do container, que tem
# ffmpeg/ffprobe). Uso:
#   bash /work/scripts/qa_probe.sh <arquivo.mp4> --platform <plataforma> [--thumb-dir <dir>]
set -euo pipefail

FILE=""
PLATFORM=""
THUMB_DIR="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform) PLATFORM="$2"; shift 2 ;;
    --thumb-dir) THUMB_DIR="$2"; shift 2 ;;
    --min-duration-override) MIN_OVERRIDE="$2"; shift 2 ;;
    -h|--help) echo "uso: qa_probe.sh <arquivo> --platform yt-long|yt_shorts|ig_reels|tiktok|ig_carousel [--thumb-dir DIR] [--min-duration-override S]"; exit 0 ;;
    *) FILE="$1"; shift ;;
  esac
done

fail() { echo "QA FAIL: $1" >&2; exit 2; }
ok()   { echo "QA OK: $1"; }

[[ -n "$FILE" && -f "$FILE" ]] || fail "arquivo de saída não informado ou inexistente ($FILE)"

# --- plataforma-alvo -----------------------------------------------
# resolution  duration_min (s)  duration_max (s)
case "$PLATFORM" in
  yt-long)      W=1920; H=1080; DMIN=600; DMAX=1200 ;;
  yt_shorts)    W=1080; H=1920; DMIN=10;  DMAX=60 ;;
  ig_reels)     W=1080; H=1920; DMIN=15;  DMAX=60 ;;
  tiktok)       W=1080; H=1920; DMIN=10;  DMAX=60 ;;
  "")           fail "plataforma obrigatória (--platform)";;
  *)            fail "plataforma desconhecida: $PLATFORM";;
esac

# override de duração mínima (smoke tests renderizam cenas curtas)
DMIN="${MIN_OVERRIDE:-$DMIN}"

# --- ffprobe checks ------------------------------------------------
# fps/frames/duration/codec
CODEC=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 "$FILE")
WIDTH=$(ffprobe  -v error -select_streams v:0 -show_entries stream=width  -of csv=p=0 "$FILE")
HEIGHT=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$FILE")
AUDIO_CODEC=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 "$FILE")
AUDIO_BITRATE=$(ffprobe -v error -select_streams a:0 -show_entries stream=bit_rate -of csv=p=0 "$FILE" | awk '{printf "%d", $1/1000}')
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$FILE")
DURATION_INT=$(printf '%.0f' "$DURATION")

# faststart: moov antes do mdat
if dd if="$FILE" bs=1 count=200000 2>/dev/null | grep -aq moov; then
  ok "faststart presente"
else
  echo "QA WARN: faststart não detectado (movflags +faststart pode ter faltado)"
fi

echo "codec=$CODEC res=${WIDTH}x${HEIGHT} audio=$AUDIO_CODEC@${AUDIO_BITRATE}kbps dur=${DURATION}s"

[[ "$CODEC" == "h264" ]] || fail "codec do vídeo não é h264 (=$CODEC)"
[[ "$AUDIO_CODEC" == "aac" ]] || fail "codec de áudio não é aac (=$AUDIO_CODEC)"
[[ "$WIDTH" -eq "$W" && "$HEIGHT" -eq "$H" ]] || fail "resolução ${WIDTH}x${HEIGHT} difere de ${W}x${H} ($PLATFORM)"
[[ "$DURATION_INT" -ge "$DMIN" && "$DURATION_INT" -le "$DMAX" ]] || \
  fail "duração ${DURATION}s fora da faixa [$DMIN, $DMAX]s de $PLATFORM"

# loudness: alvo ~ -14 LUFS (aceita margem ±3)
LOUDNESS=$(ffmpeg -hide_banner -nostats -i "$FILE" -af loudnorm=print_format=summary -f null - 2>&1 | awk '/Input Integrated/ {print $5}' | head -1)
if [[ -n "$LOUDNESS" && "$LOUDNESS" != "-inf" ]]; then
  if python3 -c "import sys; sys.exit(0 if abs(float('$LOUDNESS')-(-14))<=3.0 else 1)" 2>/dev/null; then
    ok "loudness ${LOUDNESS} LUFS dentro do tolerado (±3 de -14)"
  else
    echo "QA WARN: loudness ${LOUDNESS} LUFS fora do tolerado (alvo -14 ±3)"
  fi
else
  echo "QA WARN: não medi loudness (ffmpeg loudnorm indisponível)"
fi

# thumbnail dos primeiros 3 s
THUMB_PATH="$THUMB_DIR/thumbnail_qa.jpg"
mkdir -p "$THUMB_DIR"
ffmpeg -y -hide_banner -loglevel error -ss 2.5 -i "$FILE" -frames:v 1 "$THUMB_PATH"
[[ -s "$THUMB_PATH" ]] && ok "thumbnail extraída: $THUMB_PATH" || fail "thumbnail vazia"

# áudio presente (pelo menos 1 stream de áudio com duração > 0)
AUD_DURATION=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$FILE")
if [[ -n "$AUD_DURATION" && "$(printf '%.0f' "$AUD_DURATION")" -gt 0 ]]; then
  ok "áudio presente (${AUD_DURATION}s)"
else
  fail "stream de áudio ausente ou vazio"
fi

ok "qa_probe concluída para $PLATFORM"
