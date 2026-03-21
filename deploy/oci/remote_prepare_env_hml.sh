#!/usr/bin/env bash
set -euo pipefail

# Wrapper para gerar .env de homologacao na VM HML.
# Pode sobrescrever variaveis via env, ex:
# APP_DIR=/opt/gestao_de_apoio_arquivistico_hml HOST_IP=10.10.11.93 ./deploy/oci/remote_prepare_env_hml.sh

APP_DIR="${APP_DIR:-/opt/gestao_de_apoio_arquivistico_hml}"
HOST_IP="${HOST_IP:-10.10.11.93}"
APP_ENVIRONMENT="${APP_ENVIRONMENT:-homolog}"
APP_NAME="${APP_NAME:-Gestao de Apoio Arquivistico - Homologacao}"

export APP_DIR HOST_IP APP_ENVIRONMENT APP_NAME

"${APP_DIR}/deploy/oci/remote_prepare_env.sh"
