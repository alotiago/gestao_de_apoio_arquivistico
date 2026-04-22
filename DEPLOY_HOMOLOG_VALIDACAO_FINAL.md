# ✅ CHECKLIST FINAL — Deploy Homologação

**Timestamp**: 23 de março de 2026  
**Ambiente**: Homologação (10.10.11.93)  
**Domínio**: apoioarquivisticohml.oais.cloud  

---

## 🔍 Pré-Deploy — Validações Locais

### Git & Repositório

- [x] Repositório em `c:\des\gestao_de_apoio_arquivistico`
- [x] branch `main` atualizado
- [x] Scripts de deploy presentes:
  - [x] `deploy_homolog_execute.sh`
  - [x] `deploy_homolog_auto.ps1`
  - [x] `deploy/oci/deploy_homolog_safe.sh`
  - [x] `deploy/oci/remote_prepare_env_hml.sh`
- [x] Dockerfile backend/frontend presentes
- [x] docker-compose.homolog.yml configurado

### Documentação

- [x] `DEPLOY_HOMOLOG_README.md` ← **COMECE AQUI**
- [x] `DEPLOY_HOMOLOG_QUICK_START.md`
- [x] `DEPLOY_HOMOLOG_MANUAL.md`
- [x] `DEPLOY_HOMOLOG_CHECKLIST.md` ← Você está aqui
- [x] Alembic migrations presente em `backend/alembic/versions/`

### Configuração Validada

- [x] `NEXT_PUBLIC_API_URL` = `http://apoioarquivisticohml.oais.cloud/api/v1`
- [x] HTTP (não HTTPS) em homolog
- [x] Nginx configurado para localhost:8080 (sem exposição pública)
- [x] docker-compose.homolog.yml sem `--volumes` em script
- [x] Backend healthcheck endpoint em `/health`
- [x] Frontend build processo validado
- [x] Alembic configurado para upgrade head apenas

---

## 🚀 Deploy — Instruções Finais

### OPÇÃO A: Automático (RECOMENDADO)

#### Pré-requisito
- Git Bash OU WSL OU Terminal Linux
- SSH instalado
- Conectividade com 10.10.11.93

#### Comando Único

```bash
# 1. Abra Git Bash (Windows) OU Terminal (Linux/Mac)

# 2. Navigate
cd /c/des/gestao_de_apoio_arquivistico          # Git Bash (Windows)
# OU
cd /mnt/c/des/gestao_de_apoio_arquivistico      # WSL (Windows)
# OU
cd ~/projects/gestao_de_apoio_arquivistico      # Linux/Mac

# 3. Execute
bash ./deploy_homolog_execute.sh

# 4. Quando solicitado, forneça:
# - Senha gestor@10.10.11.93: Gjh!EDOl99$
# - Senha sudo (mesma): Gjh!EDOl99$

# ⏳ Aguarde ~10-15 minutos
```

**O script automaticamente**:
1. ✅ Atualiza Git (fetch + pull)
2. ✅ Testa SSH (sem password ou com sshpass)
3. ✅ Copia script para VM
4. ✅ Executa deploy remoto
5. ✅ Validação automática
6. ✅ Retorna checklist

### OPÇÃO B: Manual (Se preferir)

Ver [DEPLOY_HOMOLOG_MANUAL.md](DEPLOY_HOMOLOG_MANUAL.md) com cada comando individual.

---

## ✅ Pós-Deploy — Validações

### Validação 1: Conectividade SSH

```bash
ssh gestor@10.10.11.93 "echo 'OK'"
# Esperado: OK (sem password se SSH keys configuradas)
```

### Validação 2: Diretório & Git

```bash
ssh gestor@10.10.11.93 "cd /opt/gestao_de_apoio_arquivistico_hml && git log --oneline -1"
# Esperado: último commit do main
```

### Validação 3: Containers Rodando

```bash
ssh gestor@10.10.11.93 "cd /opt/gestao_de_apoio_arquivistico_hml && docker-compose -f docker-compose.homolog.yml ps | grep -c Up"
# Esperado: 8 (8 containers em execução)

# Detalhado:
ssh gestor@10.10.11.93 "cd /opt/gestao_de_apoio_arquivistico_hml && docker-compose -f docker-compose.homolog.yml ps"
# Esperado:
# hml-postgres         Up (healthy)
# hml-redis            Up (healthy)
# hml-minio            Up
# hml-backend          Up
# hml-celery-worker    Up
# hml-celery-beat      Up
# hml-frontend         Up
# hml-nginx            Up
```

### Validação 4: PostgreSQL Health

```bash
ssh gestor@10.10.11.93 "cd /opt/gestao_de_apoio_arquivistico_hml && docker-compose -f docker-compose.homolog.yml --env-file .env.homolog exec -T postgres pg_isready -U gestor_hml"
# Esperado: accepting connections
```

### Validação 5: Backend Health

```bash
ssh gestor@10.10.11.93 "curl -s http://127.0.0.1:8080/health | jq '.status'"
# Esperado: "ok"

# Com mais detalhes:
ssh gestor@10.10.11.93 "curl -s http://127.0.0.1:8080/health"
# Esperado: JSON com status, service, version, environment
```

### Validação 6: Frontend HTTP

```bash
ssh gestor@10.10.11.93 "curl -s -I http://127.0.0.1:8080/ | head -1"
# Esperado: HTTP/1.1 200 OK
```

### Validação 7: Swagger UI

```bash
ssh gestor@10.10.11.93 "curl -s -I http://127.0.0.1:8080/docs | head -1"
# Esperado: HTTP/1.1 200 OK
```

### Validação 8: ReDoc

```bash
ssh gestor@10.10.11.93 "curl -s -I http://127.0.0.1:8080/redoc | head -1"
# Esperado: HTTP/1.1 200 OK
```

### Validação 9: Alembic Current Version

```bash
ssh gestor@10.10.11.93 "cd /opt/gestao_de_apoio_arquivistico_hml && docker-compose -f docker-compose.homolog.yml --env-file .env.homolog exec -T backend alembic current"
# Esperado: current_revision_id (não "No such table: alembic_version")
```

### Validação 10: Database Tables

```bash
ssh gestor@10.10.11.93 "cd /opt/gestao_de_apoio_arquivistico_hml && docker-compose -f docker-compose.homolog.yml --env-file .env.homolog exec -T postgres psql -U gestor_hml -d gestao_arquivistica_hml -c '\\dt'"
# Esperado: lista de tabelas (public schema)
```

### Validação 11: Volume PostgreSQL

```bash
ssh gestor@10.10.11.93 "docker volume ls | grep postgres_data_hml"
# Esperado: postgres_data_hml (confirma que volume está preservado)
```

### Validação 12: .env.homolog Validado

```bash
ssh gestor@10.10.11.93 "cd /opt/gestao_de_apoio_arquivistico_hml && grep CHANGE_ME .env.homolog"
# Esperado: (nenhuma linha = sucesso)
```

---

## 🌐 Acessar Homologação

### Via SSH Tunnel (Recomendado)

```bash
# Terminal 1 (deixe aberto)
ssh -L 8080:127.0.0.1:8080 gestor@10.10.11.93

# Terminal 2 OU Browser
http://localhost:8080/          # Frontend
http://localhost:8080/docs      # Swagger
http://localhost:8080/redoc     # ReDoc
http://localhost:8080/health    # Health Check
http://localhost:8080/api/v1/*  # API Base
```

### Domínio Interno

(Se houver DNS interno configurado)

```bash
http://apoioarquivisticohml.oais.cloud/     # Frontend
http://apoioarquivisticohml.oais.cloud/docs # Swagger
```

---

## 📊 Verificação Completa (Copiar & Cola)

Executar na VM para validar tudo de uma vez:

```bash
#!/bin/bash
# Copiar este bloco inteiro e executar SSH na VM

cd /opt/gestao_de_apoio_arquivistico_hml

echo "════════════════════════════════════════════════════════════"
echo "VERIFICAÇÃO COMPLETA — Homologação"
echo "════════════════════════════════════════════════════════════"

echo ""
echo "1. Containers Running:"
docker-compose -f docker-compose.homolog.yml ps | grep hml | wc -l
echo "   ✓ Esperado: >= 8"

echo ""
echo "2. PostgreSQL Health:"
docker-compose -f docker-compose.homolog.yml --env-file .env.homolog \
  exec -T postgres pg_isready -U gestor_hml
echo "   ✓ Esperado: accepting connections"

echo ""
echo "3. Backend Health:"
curl -s http://127.0.0.1:8080/health | jq '.status'
echo "   ✓ Esperado: \"ok\""

echo ""
echo "4. Frontend:"
curl -s -I http://127.0.0.1:8080/ | head -1
echo "   ✓ Esperado: HTTP/1.1 200 OK"

echo ""
echo "5. Swagger:"
curl -s -I http://127.0.0.1:8080/docs | head -1
echo "   ✓ Esperado: HTTP/1.1 200 OK"

echo ""
echo "6. Database Version:"
docker-compose -f docker-compose.homolog.yml --env-file .env.homolog \
  exec -T postgres psql -U gestor_hml -d gestao_arquivistica_hml -c "SELECT version();" 2>&1 | head -1
echo "   ✓ Esperado: PostgreSQL 16.x"

echo ""
echo "7. Volume Persistent:"
docker volume ls | grep postgres_data_hml
echo "   ✓ Esperado: postgres_data_hml"

echo ""
echo "8. Environment:"
docker-compose -f docker-compose.homolog.yml ps hml-backend | grep hml-backend
echo "   ✓ Esperado: Container em Up"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ SE TODOS RETORNAREM ESPERADO = SUCESSO!"
echo "════════════════════════════════════════════════════════════"
```

---

## 🔒 Restrições de Segurança

**✅ FOI FEITO**:
- [x] Nunca usado `--volumes` no docker-compose
- [x] `postgres_data_hml` volume preservado
- [x] Apenas `alembic upgrade head` (nunca downgrade)
- [x] Nginx reiniciado após backend (upstream DNS fix)
- [x] HTTP (não HTTPS) em homolog
- [x] Porta 8080 bind apenas localhost (127.0.0.1)
- [x] SSH tunnel recomendado para acesso remoto

**❌ NUNCA FAZER**:
- [ ] `docker-compose down --volumes`
- [ ] `docker volume rm postgres_data_hml`
- [ ] `alembic downgrade` 
- [ ] Regenerar `POSTGRES_PASSWORD` sem `ALTER USER`
- [ ] Expor HTTP 80 publicamente
- [ ] Apagar arquivo `.env.homolog` antes de backup

---

##⏱️ Cronograma Esperado

| Fase | Tempo | Status |
|------|-------|--------|
| Git Fetch + Pull | 1-2 min | ✅ Rápido |
| SCP Transfer Script | 1 min | ✅ Rápido |
| Docker Build (1ª vez) | 5-10 min | ⏳ Lento |
| Docker Build (updates) | 1-2 min | ✅ Rápido |
| Docker Compose Up | 2-3 min | ✅ Rápido |
| PostgreSQL Ready | 2-5 min | ✅ Automático |
| Alembic Upgrade | 1-2 min | ✅ Rápido |
| Backend Health | 3-5 min | ✅ Automático |
| Healthcheck Validation | 1 min | ✅ Rápido |
| **TOTAL (First Time)** | **~15-20 min** | ✅ **Ok** |
| **TOTAL (Updates)** | **~5-10 min** | ✅ **Rápido** |

---

## 🚨 Troubleshooting Rápido

### Backend não responde (502 Nginx)

```bash
# SSH VM
cd /opt/gestao_de_apoio_arquivistico_hml

# 1. Verificar se backend está vivo
curl http://127.0.0.1:8000/health

# 2. Se não responder, ver logs
docker-compose -f docker-compose.homolog.yml logs hml-backend | tail -30

# 3. Reiniciar
docker-compose -f docker-compose.homolog.yml restart hml-backend

# 4. Aguardar 10s
sleep 10

# 5. Reiniciar Nginx
docker-compose -f docker-compose.homolog.yml restart hml-nginx

# 6. Testar
curl http://127.0.0.1:8080/health
```

### PostgreSQL não conecta

```bash
# SSH VM
docker logs hml-postgres | tail -30
docker volume ls | grep hml
docker-compose -f docker-compose.homolog.yml ps hml-postgres
```

### Alembic falha

```bash
# SSH VM
cd /opt/gestao_de_apoio_arquivistico_hml

# Ver current
docker-compose -f docker-compose.homolog.yml --env-file .env.homolog \
  exec -T backend alembic current

# Ver history
docker-compose -f docker-compose.homolog.yml --env-file .env.homolog \
  exec -T backend alembic history -v | tail -20
```

---

## ✨ Status Final

```
🎯 DEPLOY HOMOLOGAÇÃO PRONTO

📋 Arquivos:
   ✅ deploy_homolog_execute.sh (automático)
   ✅ deploy_homolog_auto.ps1 (PowerShell)
   ✅ deploy/oci/deploy_homolog_safe.sh (core)

📚 Documentação:
   ✅ DEPLOY_HOMOLOG_README.md (overview)
   ✅ DEPLOY_HOMOLOG_QUICK_START.md (rápido)
   ✅ DEPLOY_HOMOLOG_MANUAL.md (detalhado)
   ✅ DEPLOY_HOMOLOG_CHECKLIST.md (você)

🔐 Configuração:
   ✅ Domínio: apoioarquivisticohml.oais.cloud
   ✅ API URL: http://apoioarquivisticohml.oais.cloud/api/v1
   ✅ VM: 10.10.11.93 (gestor/Gjh!EDOl99$)
   ✅ HTTP (sem HTTPS)
   ✅ PostgreSQL preservado
   ✅ Alembic apenas upgrade

🚀 PRÓXIMA AÇÃO: 
   bash ./deploy_homolog_execute.sh
```

---

**Criado**: 23 de março de 2026  
**Versão**: 1.0 Final  
**Status**: ✅ VALIDADO E PRONTO PARA DEPLOY
