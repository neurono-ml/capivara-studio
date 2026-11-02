#!/usr/bin/env bash
# validate_env.sh — pré-checagem simples antes de usar a skill.
# Não exibe segredos, apenas informa se estão presentes.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${CAPY_IMAGE:-ghcr.io/neurono-ml/capivara-studio-runner:latest}"
EXIT=0

ok()   { echo "ok   $1"; }
warn() { echo "warn $1"; EXIT=1; }

# 1. runtime de container
if command -v docker >/dev/null 2>&1; then
  ok "container runtime: docker (v$(docker --version 2>/dev/null | awk '{gsub(",",""); print $3}'))"
elif command -v podman >/dev/null 2>&1; then
  ok "container runtime: podman ($(podman --version 2>/dev/null))"
else
  warn "nenhum container runtime (docker/podman) encontrado"
fi

# 2. imagem presente; senão tenta pull
if command -v docker >/dev/null 2>&1; then
  if docker image inspect "$IMAGE" >/dev/null 2>&1; then
    ok "imagem presente: $IMAGE"
  else
    warn "imagem não presente: $IMAGE (tento pull automaticamente)"
    docker pull "$IMAGE" >/dev/null 2>&1 && ok "pull efetuado: $IMAGE" || warn "pull falhou para $IMAGE"
  fi
elif command -v podman >/dev/null 2>&1; then
  if podman image exists "$IMAGE" 2>/dev/null; then
    ok "imagem presente: $IMAGE"
  else
    warn "imagem não presente: $IMAGE"
  fi
fi

# 3. brand local
BRAND_HOST="${CAPY_BRAND_DIR:-$SKILL_DIR/brand/brand.local.json}"
if [[ -f "$BRAND_HOST" ]]; then
  ok "brand local presente: $BRAND_HOST"
elif [[ -f "$SKILL_DIR/templates/brand.example.json" ]]; then
  warn "brand.local.json ausente; uso brand.example.json genérico"
else
  warn "brand ausente e brand.example.json ausente"
fi

# 4. TTS key presente (não exibir a chave)
if [[ -n "${TTS_API_KEY:-}" ]]; then
  ok "TTS_API_KEY definida"
else
  warn "TTS_API_KEY não definida (etapa voice-director falha sem ela)"
fi
if [[ -n "${TTS_PROVIDER:-}" ]]; then
  ok "TTS_PROVIDER definido (${TTS_PROVIDER})"
else
  warn "TTS_PROVIDER não definido (esperado: openai | elevenlabs | compatível)"
fi

# 5. ffmpeg host (não obrigatório; runner traz ffmpeg)
if command -v ffmpeg >/dev/null 2>&1; then
  ok "ffmpeg host presente (opcional)"
else
  ok "ffmpeg host ausente — ok, pipeline roda ffmpeg dentro do container"
fi

if [[ $EXIT -ne 0 ]]; then
  echo "resultado: ambiente com warnings — ver itens 'warn' acima"
fi
exit $EXIT
