#!/usr/bin/env bash
# docker-run.sh — wrapper para comandos dentro do container capivara-studio-runner.
# Monta output/rw, scripts (ro), referências (ro) e brand local (ro). Preserva uid:gid do host.
#
# Uso: scripts/docker-run.sh <comando> [args...]
# Exemplo: scripts/docker-run.sh python /work/scripts/render_manim.py --scenes /work/output/abc/scenes
#
# Env:
#   CAPY_IMAGE           override da imagem (default ghcr.io/neurono-ml/capivara-studio-runner:latest)
#   CAPY_SESSION_DIR     diretório da sessão no host (default ./output/<CAPY_SESSION_ID>)
#   CAPY_SESSION_ID      id da sessão (default "default")
#   CAPY_BRAND_DIR       diretório da marca no host (default ./brand)
#   CAPY_KEEP_TTY=1      modo interativo (docker -it)
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER_WORK="/work"
IMAGE="${CAPY_IMAGE:-ghcr.io/neurono-ml/capivara-studio-runner:latest}"
SESSION_ID="${CAPY_SESSION_ID:-default}"
SESSION_DIR_HOST="${CAPY_SESSION_DIR:-$SKILL_DIR/output/$SESSION_ID}"
BRAND_DIR_HOST="${CAPY_BRAND_DIR:-$SKILL_DIR/brand}"

mkdir -p "$SESSION_DIR_HOST"

# Auto-detecção docker/podman (docker tem prioridade)
if command -v docker >/dev/null 2>&1; then
  DOCKER_CMD=(docker)
elif command -v podman >/dev/null 2>&1; then
  DOCKER_CMD=(podman)
else
  echo "erro: nenhum container runtime encontrado (docker ou podman)" >&2
  exit 1
fi

# uid:gid do host (permite escrever no output ainda que de dentro de container rootless)
HOST_UID="$(id -u)"
HOST_GID="$(id -g)"

# Montagens:
#   /work/output   → output da sessão (rw)
#   /work/scripts  → scripts da skill (ro): render_manim.py, manim_skills/, shell scripts
#   /work/references → referências (ro, para consulta do CLI)
#   /work/brand    → brand local (ro) — nunca copiado para a imagem
ARGS=(
  run --rm
  -u "${HOST_UID}:${HOST_GID}"
  -v "$SESSION_DIR_HOST:$CONTAINER_WORK/output"
  -v "$SKILL_DIR/scripts:$CONTAINER_WORK/scripts:ro"
  -v "$SKILL_DIR/references:$CONTAINER_WORK/references:ro"
)

if [[ -d "$BRAND_DIR_HOST" ]]; then
  ARGS+=( -v "$BRAND_DIR_HOST:$CONTAINER_WORK/brand:ro" )
fi

# TTY apenas se stdin e stdout forem terminais ou CAPY_KEEP_TTY=1.
if [[ "${CAPY_KEEP_TTY:-0}" == "1" || ( -t 0 && -t 1 ) ]]; then
  ARGS+=( -i -t )
fi

exec "${DOCKER_CMD[@]}" "${ARGS[@]}" "$IMAGE" "$@"

# docker:start-lock — evita corrida em builds concorrentes (single-file lock)
"${DOCKER_CMD[@]}" "${ARGS[@]}" "$IMAGE" "$@"
