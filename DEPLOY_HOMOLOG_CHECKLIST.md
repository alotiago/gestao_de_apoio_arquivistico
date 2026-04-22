# Deploy Homologação - Gestao de Apoio Arquivistico

**Data**: 23 de março de 2026
**Ambiente**: Homologação  
**VM**: 10.10.11.93  
**Domínio**: apoioarquivisticohml.oais.cloud  
**Usuário**: gestor  
**App Dir**: /opt/gestao_de_apoio_arquivistico_hml  

---

## 📋 Pré-requisitos

- [x] Domínio resolvido para `apoioarquivisticohml.oais.cloud` → 10.10.11.93
- [x] SSH acionado para gestor@10.10.11.93
- [x] Docker + Docker Compose instalados na VM
- [x] Git atualizado
- [x] Backup de dados existentes (se houver) em `postgres_data_hml`

---

## 🚀 Etapas de Deploy

### 1️⃣ Atualizar Repositório

```bash
cd /opt/gestao_de_apoio_arquivistico_hml
git fetch origin main
git checkout main
git pull --ff-only origin main
```

**Status**: ⏳ Aguardando

---

### 2️⃣ Preparar .env.homolog

**Variáveis Obrigatórias**:

```bash
NEXT_PUBLIC_API_URL=http://apoioarquivisticohml.oais.cloud/api/v1

POSTGRES_DB=gestao_arquivistica_hml
POSTGRES_USER=gestor_hml
POSTGRES_PASSWORD=<PRESERVAR_EXISTENTE_OU_NOVO>

REDIS_PASSWORD=<GERAR_SE_NOVO>
CELERY_RESULT_BACKEND=redis://:${REDIS_PASSWORD}@redis:6379/2

JWT_SECRET_KEY=<GERAR_SE_NOVO>
JWT_REFRESH_SECRET_KEY=<GERAR_SE_NOVO>

MINIO_ROOT_USER=minioadmin_hml
MINIO_ROOT_PASSWORD=<GERAR_SE_NOVO>

NGINX_BIND=127.0.0.1:8080:80
ENVIRONMENT=homolog
```

**Validação**: ✅ Sem `CHANGE_ME`

**Status**: ⏳ Aguardando

---

### 3️⃣ Build Docker

```bash
cd /opt/gestao_de_apoio_arquivistico_hml
sudo docker compose -f docker-compose.homolog.yml --env-file .env.homolog build
```

**Tempo Estimado**: 5-10 minutos  
**Status**: ⏳ Aguardando

---

### 4️⃣ Deploy Stack (SEM `--volumes`)

```bash
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  up -d --remove-orphans
```

⚠️ **IMPORTANTE**: NUNCA usar `--volumes` — apagaria `postgres_data_hml` irreversivelmente!

**Containers Esperados**:
- `hml-postgres` ✓
- `hml-redis` ✓
- `hml-minio` ✓
- `hml-backend` ✓
- `hml-celery-worker` ✓
- `hml-celery-beat` ✓
- `hml-frontend` ✓
- `hml-nginx` ✓

**Status**: ⏳ Aguardando

---

### 5️⃣ Aguardar Saúde dos Serviços

```bash
# Verificar PostgreSQL
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  exec -T postgres pg_isready -U gestor_hml
```

**Status**: ⏳ Aguardando

---

### 6️⃣ Executar Alembic Upgrade (SEM downgrade!)

```bash
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  exec -T backend alembic upgrade head
```

⚠️ **IMPORTANTE**: Apenas `upgrade head` — jamais downgrade em producção/homolog!

**Status**: ⏳ Aguardando

---

### 7️⃣ Validar Healthcheck

```bash
# Via SSH Tunnel (local):
curl -v http://127.0.0.1:8080/health

# Ou verificar internamente:
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  exec -T backend curl http://localhost:8000/health
```

**Resposta Esperada**:
```json
{
  "status": "ok",
  "service": "gestao-arquivistica",
  "version": "0.1.0",
  "environment": "homolog"
}
```

**Status**: ⏳ Aguardando

---

### 8️⃣ Validar Acesso

**Frontend**:
```bash
curl -v http://127.0.0.1:8080/
# Esperar HTML (status 200)
```

**API Docs**:
```bash
curl -v http://127.0.0.1:8080/docs
# Esperar Swagger UI (status 200)
```

**Status**: ⏳ Aguardando

---

### 9️⃣ Reiniciar Nginx (se necessário)

```bash
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  restart hml-nginx
```

**Motivo**: Após recrear backend/celery, DNS/upstream pode ficar desatualizado.

**Status**: ⏳ Aguardando

---

## ✅ Checklist Final

- [ ] Git atualizado em main
- [ ] `.env.homolog` validado (sem `CHANGE_ME`)
- [ ] Docker compose build completo
- [ ] `docker compose up -d --remove-orphans` executado (SEM `--volumes`)
- [ ] Todos os 8 containers rodando (`hml-*`)
- [ ] PostgreSQL health OK
- [ ] `alembic upgrade head` sem erros
- [ ] `/health` respondendo com status `ok`
- [ ] Frontend acessível em raiz `/`
- [ ] Swagger UI rodando em `/docs`

## 📊 Status Geral

**Fase**: Preparação  
**Última Atualização**: 2026-03-23 00:00:00  
**Resultado**: ⏳ PENDENTE

---

## 🔒 Restrições Obrigatórias

✅ **NUNCA**:
- [ ] Usar `docker compose ... --volumes`
- [ ] Remover `postgres_data_hml` manualmente
- [ ] Executar `downgrade` com Alembic
- [ ] Regenerar `POSTGRES_PASSWORD` sem `ALTER USER` no banco
- [ ] Expor porta 80 publicamente (usar SSH tunnel)
- [ ] Usar HTTPS em homolog (apenas HTTP)

---

## 🚨 Se Der Erros

### Backend não inicia
```bash
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  logs hml-backend --tail=50
```

### Nginx retorna 502/504
```bash
# Reiniciar Nginx
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  restart hml-nginx
```

### Banco não conecta
```bash
# Verificar credenciais em .env.homolog
# Verificar se postgres_data_hml existe
sudo docker volume ls | grep hml
```

### Alembic falha
```bash
# Verificar version metadata
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  exec -T backend alembic current
```

---

**Próxima Ação**: Conectar via SSH e executar deploy.md
