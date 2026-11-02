#!/usr/bin/env bash
# build.sh — build local da imagem runner (multi-arch é feito no CI; local é amd64)
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${CAPY_IMAGE:-ghcr.io/neurono-ml/capivara-studio-runner:latest}"

# contexto de build precisa enxergar scripts/, templates/, references/, docker/
cd "$SKILL_DIR"

# auto-detecção docker/podman (docker primeiro)
if command -v docker >/dev/null 2>&1; then
  CMD=(docker)
elif command -v podman >/dev/null 2>&1; then
  CMD=(podman)
else
  echo "erro: docker ou podman não encontrados" >&2
  exit 1
fi

echo "building ${IMAGE} (contexto: ${SKILL_DIR})"
"${CMD[@]}" build \
  -f docker/Dockerfile \
  -t "$IMAGE" \
  .

echo "build concluído: ${IMAGE}"
