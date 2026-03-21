#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   sudo ./deploy/oci/enable_https_letsencrypt.sh -d app.exemplo.com [-e voce@exemplo.com]

APP_DIR="${APP_DIR:-/opt/gestao_de_apoio_arquivistico}"
DOMAIN=""
EMAIL=""

while getopts ":d:e:" opt; do
  case "$opt" in
    d) DOMAIN="$OPTARG" ;;
    e) EMAIL="$OPTARG" ;;
    *)
      echo "Uso: $0 -d dominio [-e email]"
      exit 1
      ;;
  esac
done

if [[ -z "$DOMAIN" ]]; then
  echo "Uso: $0 -d dominio [-e email]"
  exit 1
fi

if [[ ! -d "$APP_DIR" ]]; then
  echo "Diretorio da app nao encontrado: $APP_DIR"
  exit 1
fi

log() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Comando ausente: $1"
    exit 1
  }
}

need docker
need curl

log "Instalando certbot (se necessario)"
apt-get update -y
apt-get install -y certbot

DOMAIN_IPS="$(getent ahostsv4 "$DOMAIN" | awk '{print $1}' | sort -u | tr '\n' ' ')"
HTTP_CODE="$(curl -s -o /dev/null -w '%{http_code}' "http://$DOMAIN/health" || true)"

log "Validando DNS e acesso HTTP atual"
echo "Dominio: $DOMAIN"
echo "IPs do dominio: $DOMAIN_IPS"
echo "HTTP atual em /health: $HTTP_CODE"

if [[ ! "$HTTP_CODE" =~ ^(200|301|302|307|308)$ ]]; then
  echo "ERRO: o dominio ainda nao responde /health com HTTP valido (2xx/3xx)."
  echo "Ajuste NAT/DNS/publicacao e rode novamente."
  exit 1
fi

cd "$APP_DIR"

log "Parando nginx para desafio standalone"
docker compose -f docker-compose.oci.yml stop nginx || true

log "Emitindo certificado Let's Encrypt"
CERTBOT_ARGS=(
  certonly
  --standalone
  --non-interactive
  --agree-tos
  -d "$DOMAIN"
  --keep-until-expiring
)

if [[ -n "$EMAIL" ]]; then
  CERTBOT_ARGS+=(--email "$EMAIL")
else
  CERTBOT_ARGS+=(--register-unsafely-without-email)
fi

certbot "${CERTBOT_ARGS[@]}"

log "Gerando configuracao nginx com HTTPS"
cat > "$APP_DIR/deploy/oci/nginx.conf" <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    client_max_body_size 50m;
    proxy_connect_timeout 30s;
    proxy_send_timeout 120s;
    proxy_read_timeout 120s;

    location /api/v1/ {
        proxy_pass http://backend:8000/api/v1/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location = /health {
        proxy_pass http://backend:8000/health;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    location = /ready {
        proxy_pass http://backend:8000/ready;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    location = /openapi.json {
        proxy_pass http://backend:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    location /docs {
        proxy_pass http://backend:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    location = /docs/swagger-initializer.js {
        proxy_pass http://backend:8000/docs/swagger-initializer.js;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    location /redoc {
        proxy_pass http://backend:8000/redoc;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    location /_static/swagger-ui/ {
        proxy_pass http://backend:8000/_static/swagger-ui/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    location = /robots.txt {
        proxy_pass http://backend:8000/robots.txt;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    location = /sitemap.xml {
        proxy_pass http://backend:8000/sitemap.xml;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
    }

    location / {
        proxy_pass http://frontend:4000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

log "Subindo nginx com HTTPS"
docker compose -f docker-compose.oci.yml up -d --no-build nginx

log "Configurando renovacao automatica"
cat > /etc/cron.d/gaa-certbot-renew <<EOF
SHELL=/bin/bash
PATH=/usr/sbin:/usr/bin:/sbin:/bin
0 3 * * * root certbot renew --quiet --pre-hook "cd $APP_DIR && docker compose -f docker-compose.oci.yml stop nginx" --post-hook "cd $APP_DIR && docker compose -f docker-compose.oci.yml up -d --no-build nginx"
EOF
chmod 644 /etc/cron.d/gaa-certbot-renew

log "Teste final"
curl -I "https://$DOMAIN/health" || true

echo "HTTPS habilitado em: https://$DOMAIN"
