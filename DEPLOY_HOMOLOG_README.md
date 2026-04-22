# 🎯 DEPLOY HOMOLOGAÇÃO — RESUMO EXECUTIVO

**Status**: ✅ **PRONTO PARA IR AO AR**

---

## 📋 O QUE FOI FEITO

### ✅ Investigação Completa
- Analisado `docker-compose.homolog.yml`
- Validado arquivo `.env.homolog` (template)
- Entendido fluxo Nginx → Frontend/Backend
- Mapeado alembic upgrade head
- Confirmado: VM 10.10.11.93 com duas aplicações coexistindo

### ✅ Scripts Prontos
| Arquivo | Propósito | Como Usar |
|---------|----------|----------|
| `deploy_homolog_execute.sh` | Deploy automático (bash) | `bash ./deploy_homolog_execute.sh` |
| `deploy_homolog_auto.ps1` | Deploy automático (PowerShell) | `powershell -File deploy_homolog_auto.ps1` |
| `deploy/oci/deploy_homolog_safe.sh` | Core remoto | Executado automaticamente via SSH |

### ✅ Documentação
| Arquivo | Conteúdo |
|---------|----------|
| `DEPLOY_HOMOLOG_QUICK_START.md` | 📌 **USE ESTA PRIMEIRO** — Guia rápido |
| `DEPLOY_HOMOLOG_MANUAL.md` | Passo a passo completo (opção manual) |
| `DEPLOY_HOMOLOG_CHECKLIST.md` | Checklist detalhado com restrições |

### ✅ Proteções Aplicadas
- ❌ **Nunca `--volumes`** — `postgres_data_hml` preservado
- ❌ **Nunca `downgrade` alembic** — Apenas `upgrade head`
- ✅ **Nginx reiniciado** — Após recrear backend (upstream DNS fix)
- ✅ **Senha PostgreSQL preservada** — Se banco existir
- ✅ **HTTP (não HTTPS)** — Conforme requerimento
- ✅ **SSH tunnel** — Recomendado para acesso

---

## 🚀 EXECUTE AGORA

### Opção 1: Automático (RECOMENDADO) — ~15 minutos

```bash
# Git Bash OU WSL OU Terminal Linux

# Navegar ao projeto
cd /c/des/gestao_de_apoio_arquivistico  # Git Bash
# OU
cd /mnt/c/des/gestao_de_apoio_arquivistico  # WSL

# Executar deploy
bash ./deploy_homolog_execute.sh

# Aguardar conclusão
# O script irá:
#  1. Atualizar git
#  2. Copiar script para VM
#  3. Executar deploy (solicitará sudo password)
#  4. Validar healthcheck
#  5. Listar containers
```

### Opção 2: Manual Passo-a-Passo

Ver [DEPLOY_HOMOLOG_MANUAL.md](DEPLOY_HOMOLOG_MANUAL.md) para lista completa de comandos.

---

## ✅ VALIDAÇÃO PÓS-DEPLOY

Após conclusão, executar via SSH:

```bash
ssh gestor@10.10.11.93
cd /opt/gestao_de_apoio_arquivistico_hml

# Checklist rápido
echo "[1] Containers:" && docker compose -f docker-compose.homolog.yml ps | grep -c Up
echo "[2] PG Health:" && docker compose -f docker-compose.homolog.yml --env-file .env.homolog exec -T postgres pg_isready -U gestor_hml
echo "[3] API Health:" && curl -s http://127.0.0.1:8080/health | jq '.status'
echo "[4] Frontend:" && curl -s -I http://127.0.0.1:8080/ | head -1
echo "[5] Swagger:" && curl -s -I http://localhost:8080/docs | head -1

# Esperado: ✓ 8+ containers Up | ✓ "ok" | ✓ HTTP/1.1 200 OK (x3)
```

---

## 📊 Acessar Homologação

### Via SSH Tunnel (Seguro)

```bash
# Terminal local — abrir tunnel
ssh -L 8080:127.0.0.1:8080 gestor@10.10.11.93

# Browser — acessar
http://localhost:8080/          # Frontend
http://localhost:8080/docs      # Swagger
http://localhost:8080/redoc     # ReDoc
http://localhost:8080/health    # Health Check
http://localhost:8080/api/v1/*  # API calls
```

### Monitorar Logs

```bash
ssh gestor@10.10.11.93
cd /opt/gestao_de_apoio_arquivistico_hml
docker compose -f docker-compose.homolog.yml logs -f hml-backend
```

---

## 🔐 Credenciais & Configuração

| Item | Valor |
|------|-------|
| **VM IP** | 10.10.11.93 |
| **VM User** | gestor |
| **VM Password** | Gjh!EDOl99$ |
| **App Dir** | /opt/gestao_de_apoio_arquivistico_hml |
| **Domínio** | apoioarquivisticohml.oais.cloud |
| **API URL** | http://apoioarquivisticohml.oais.cloud/api/v1 |
| **Nginx Bind** | 127.0.0.1:8080 (localhost only) |
| **Protocol** | HTTP (não HTTPS) |
| **Database** | gestao_arquivistica_hml |
| **DB User** | gestor_hml |
| **Containers** | hml-* (existem 8) |

---

## ⏱️ Cronograma

| Fase | Tempo | Status |
|------|-------|--------|
| Git Update | 1-2 min | ✅ Automático |
| SCP Transfer | 1-2 min | ✅ Automático |
| Docker Build | 5-10 min | ⏳ Primeiro deploy |
| Docker Up | 2-3 min | ✅ Rápido |
| Alembic Upgrade | 1-2 min | ✅ Rápido |
| Healthcheck | 2-3 min | ✅ Validação |
| **TOTAL** | **~15 min** | ✅ First Time |

---

## 🚨 Se Algo Der Errado

### Backend não responde

```bash
ssh gestor@10.10.11.93
cd /opt/gestao_de_apoio_arquivistico_hml
docker compose -f docker-compose.homolog.yml logs hml-backend | tail -50
```

### Nginx 502

```bash
# Reiniciar backend + nginx
docker compose -f docker-compose.homolog.yml restart hml-backend hml-nginx
sleep 10
curl http://127.0.0.1:8080/health
```

### Alembic falha

```bash
docker compose -f docker-compose.homolog.yml --env-file .env.homolog \
  exec -T backend alembic current
docker compose -f docker-compose.homolog.yml --env-file .env.homolog \
  exec -T backend alembic history -v | tail -20
```

Ve [DEPLOY_HOMOLOG_MANUAL.md](DEPLOY_HOMOLOG_MANUAL.md) para mais troubleshooting.

---

## 📝 Checklist Pré-Deploy

- [x] Domínio `apoioarquivisticohml.oais.cloud` resolvido → 10.10.11.93
- [x] SSH conectividade testada
- [x] Docker/Compose instalados na VM
- [x] `/opt/gestao_de_apoio_arquivistico_hml` existe
- [x] `postgres_data_hml` volume protegido (nunca --volumes)
- [x] Git main atualizado
- [x] Scripts prontos
- [x] Documentação preparada

---

## 🎯 Próximos Passos

1. **Imediatamente**:
   ```bash
   bash ./deploy_homolog_execute.sh
   ```

2. **Após conclusão**:
   ```bash
   ssh -L 8080:127.0.0.1:8080 gestor@10.10.11.93
   # Depois acesse http://localhost:8080/ no navegador
   ```

3. **Para redeployments**:
   ```bash
   # Simples: git pull + compose restart
   git pull origin main
   docker compose -f docker-compose.homolog.yml up -d --remove-orphans
   ```

---

## 📞 Support

**Documentação**:
- `/opt/gestao_de_apoio_arquivistico_hml/docs/LOCAL_DEV.md` (na VM)
- `DEPLOY_HOMOLOG_MANUAL.md` (este repositório)
- `DEPLOY_HOMOLOG_CHECKLIST.md` (este repositório)

**Logs**:
```bash
cd /opt/gestao_de_apoio_arquivistico_hml
docker compose -f docker-compose.homolog.yml logs -f [service]
```

---

## ✨ TL;DR

```bash
# 1. Git Bash
bash ./deploy_homolog_execute.sh

# 2. Aguarde ~15 min

# 3. SSH Tunnel
ssh -L 8080:127.0.0.1:8080 gestor@10.10.11.93

# 4. Acesse
http://localhost:8080/
```

---

**Última Atualização**: 23 de março de 2026  
**Preparado por**: Deploy Pipeline Automatizado  
**Status**: ✅ **PRONTO PARA PRODUÇÃO (HOMOLOG)**
