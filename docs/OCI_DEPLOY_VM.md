# Deploy na Oracle Cloud (OCI) - Gestao de Apoio Arquivistico

Guia para publicar o projeto em uma VM Ubuntu na OCI usando Docker Compose em modo producao.

## 1. Requisitos de infraestrutura

- OS da VM: `Ubuntu 24.04 LTS` (validado) ou `Ubuntu 22.04 LTS`
- Recursos recomendados: `4 vCPU`, `8 GB RAM`, `80 GB SSD`
- Recursos minimos: `2 vCPU`, `4 GB RAM`, `30 GB SSD`

Portas:

- Externas: `22/tcp`, `80/tcp`, `443/tcp`
- Internas: `5432` (Postgres), `6379` (Redis), `9000/9001` (MinIO), `3310` (ClamAV), `8000` (backend), `4000` (frontend)

## 2. Arquivos adicionados para OCI

- `docker-compose.oci.yml`
- `.env.oci.example`
- `deploy/oci/nginx.conf`
- `deploy/oci/deploy_vm.sh`

## 3. Provisionar VM na OCI

No Security List / NSG, liberar:

- Ingress `22/tcp` (restrito ao seu IP)
- Ingress `80/tcp`
- Ingress `443/tcp`

## 4. Deploy na VM

### 4.1 Acessar por SSH

```bash
ssh ubuntu@SEU_IP_PUBLICO
```

### 4.2 Clonar repositorio

```bash
sudo apt-get update -y
sudo apt-get install -y git

git clone https://github.com/SEU_USUARIO/gestao_de_apoio_arquivistico.git
cd gestao_de_apoio_arquivistico
```

### 4.3 Configurar variaveis

```bash
cp .env.oci.example .env
nano .env
```

Valores obrigatorios no `.env`:

- `NEXT_PUBLIC_API_URL` (ex: `http://SEU_IP_PUBLICO/api/v1`)
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `MINIO_ROOT_PASSWORD`
- `JWT_SECRET_KEY`
- `JWT_REFRESH_SECRET_KEY`
- `CORS_ORIGINS`

### 4.4 Executar script de deploy

```bash
chmod +x deploy/oci/deploy_vm.sh
sudo APP_DIR=/opt/gestao_de_apoio_arquivistico REPO_URL=https://github.com/SEU_USUARIO/gestao_de_apoio_arquivistico.git BRANCH=main ./deploy/oci/deploy_vm.sh
```

Se o repositorio ja estiver em `/opt/gestao_de_apoio_arquivistico`, pode executar sem `REPO_URL`.

### 4.5 Reset completo e subida do zero

Quando o ambiente estiver instavel e for melhor recriar apenas o GAA do zero na VM, use:

```bash
cd /opt/gestao_de_apoio_arquivistico
chmod +x deploy/oci/reset_and_redeploy_vm.sh

sudo APP_DIR=/opt/gestao_de_apoio_arquivistico \
	REPO_URL=https://github.com/SEU_USUARIO/gestao_de_apoio_arquivistico.git \
	BRANCH=main \
	APP_DOMAIN=apoioarquivistico.oais.cloud \
	NGINX_BIND=127.0.0.1:8080:80 \
	HEALTHCHECK_URL=http://127.0.0.1:8080/health \
	PURGE_APP_DIR=true \
	./deploy/oci/reset_and_redeploy_vm.sh
```

Esse reset:

- Derruba apenas a stack do GAA.
- Remove volumes, containers e imagens do GAA.
- Preserva a outra aplicacao da VM.
- Recria o `.env` com dominio publico e bind interno em `127.0.0.1:8080`.
- Sobe tudo novamente e aplica migrations.

## 5. Validacao

```bash
curl -I http://SEU_IP_PUBLICO/
curl http://SEU_IP_PUBLICO/health
curl http://SEU_IP_PUBLICO/docs
```

Esperado:

- Frontend responde `200`
- Health responde JSON com `status`
- Docs abre Swagger

## 6. Operacao

```bash
cd /opt/gestao_de_apoio_arquivistico

docker compose -f docker-compose.oci.yml ps
docker compose -f docker-compose.oci.yml logs -f

docker compose -f docker-compose.oci.yml exec -T backend alembic upgrade head
```

## 7. HTTPS (recomendado)

Depois de apontar DNS para o IP da VM:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

## 8. Observacoes importantes

- O frontend precisa de `NEXT_PUBLIC_API_URL` correto no build, por isso foi adicionado `ARG` no `frontend/Dockerfile`.
- O `CELERY_RESULT_BACKEND` deve ficar em `redis://.../2` para evitar queda do worker por backend padrao incorreto.
- O MinIO Console fica ligado apenas em `127.0.0.1:9001` (acesso com SSH tunnel, se necessario).
- Na VM `10.10.11.92`, o GAA deve publicar o nginx do container em `127.0.0.1:8080:80` e ficar atras do nginx do host.
- Para esse cenario, o `HEALTHCHECK_URL` do deploy deve ser `http://127.0.0.1:8080/health`.

## 9. Homologacao (VM separada)

Para homologacao em VM dedicada (exemplo: `10.10.11.93`):

```bash
sudo APP_DIR=/opt/gestao_de_apoio_arquivistico_hml REPO_URL=https://github.com/SEU_USUARIO/gestao_de_apoio_arquivistico.git BRANCH=main ./deploy/oci/deploy_vm.sh

sudo APP_DIR=/opt/gestao_de_apoio_arquivistico_hml HOST_IP=10.10.11.93 APP_ENVIRONMENT=homolog APP_NAME="Gestao de Apoio Arquivistico - Homologacao" ./deploy/oci/remote_prepare_env.sh

cd /opt/gestao_de_apoio_arquivistico_hml
sudo docker compose -f docker-compose.oci.yml up -d --build
sudo docker compose -f docker-compose.oci.yml exec -T backend alembic upgrade head
```

Validacao HML:

```bash
curl http://10.10.11.93/health
curl -I http://10.10.11.93/
```
