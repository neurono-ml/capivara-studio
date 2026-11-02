#!/usr/bin/env bash
# smoke-test.sh — builda (se preciso) e valida a imagem: render de um config de
# exemplo mínimo (text_callout ~3s) + qa_probe na saída.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${CAPY_IMAGE:-ghcr.io/neurono-ml/capivara-studio-runner:latest}"
SMOKE_DIR="${SMOKE_DIR:-$(mktemp -d /tmp/capy-smoke-XXXX)}"
PLATFORM="${PLATFORM:-yt-long}"

echo "smoke: dir temporário ${SMOKE_DIR}"

# imagem presente? senão pull
RUNTIME=docker
if ! command -v docker >/dev/null 2>&1; then
  RUNTIME=podman
fi
if ! $RUNTIME image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "smoke: imagem ausente, fazendo pull de ${IMAGE}"
  $RUNTIME pull "$IMAGE"
fi

mkdir -p "$SMOKE_DIR/scenes" "$SMOKE_DIR/final"

# 1. config mínimo (text_callout 3s, cores genéricas)
cat > "$SMOKE_DIR/scenes/smoke.json" <<'JSON'
{
  "id": "smoke-001",
  "scene_type": "text_callout",
  "output_format": "video",
  "resolution": [1920, 1080],
  "duration": 3.0,
  "platform": "yt-long",
  "brand": "/work/templates/brand.example.json",
  "params": {
    "text": "Smoke test do capivara-studio",
    "position": "center",
    "mascot": false
  }
}
JSON

# 2. render via runner (mesma montagem de docker-run.sh, mas com dirs do smoke)
$RUNTIME run --rm \
  -v "$SMOKE_DIR:$SMOKE_DIR" \
  -w "$SMOKE_DIR" \
  -e SCENE_CONFIG="$SMOKE_DIR/scenes/smoke.json" \
  -e PYTHONPATH=/work/scripts \
  -e HOME=/tmp \
  -u "$(id -u):$(id -g)" \
  "$IMAGE" \
  --config "$SMOKE_DIR/scenes/smoke.json" --out "$SMOKE_DIR/rendered" \
  --skip-failed || { echo "smoke FAIL: render_manim retornou erro"; exit 1; }

# 3. localizar vídeo renderizado
RENDERED=$(find "$SMOKE_DIR/rendered" -name "smoke-001*.mp4" 2>/dev/null | head -1)
if [[ -z "$RENDERED" ]]; then
  echo "smoke FAIL: MP4 não encontrado" >&2
  find "$SMOKE_DIR/rendered" | head -20
  exit 1
fi
echo "smoke: renderizado ${RENDERED}"

# 4. montagem mínima cena → final com H.264/faststart
#    (a cena do smoke não tem áudio; qa_probe exige áudio, então adicionamos
#     trilha silenciosa para representar o pipeline completo)
FINAL="$SMOKE_DIR/final/smoke.mp4"
$RUNTIME run --rm \
  -v "$SMOKE_DIR:$SMOKE_DIR" -w "$SMOKE_DIR" \
  -e HOME=/tmp -u "$(id -u):$(id -g)" \
  --entrypoint bash \
  "$IMAGE" \
  -c "ffmpeg -y -hide_banner -loglevel error -i 'rendered/$(basename "$RENDERED")' \
       -f lavfi -i anullsrc=r=48000:cl=stereo \
       -shortest -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart \
       -c:a aac -b:a 192k -ar 48000 -t 3 final/smoke.mp4"

# 5. qa_probe dentro do container
$RUNTIME run --rm \
  -v "$SMOKE_DIR:$SMOKE_DIR" -w "$SMOKE_DIR" \
  -e HOME=/tmp -u "$(id -u):$(id -g)" \
  --entrypoint bash \
  "$IMAGE" \
  "/work/scripts/qa_probe.sh" "final/smoke.mp4" --platform "$PLATFORM" \
  --thumb-dir final --min-duration-override 1

echo "smoke OK"
