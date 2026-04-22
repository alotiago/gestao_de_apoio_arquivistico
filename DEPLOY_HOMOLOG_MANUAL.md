# 🚀 DEPLOY HOMOLOGAÇÃO — Instruções Finais (Passo a Passo)

**Data**: 23 de março de 2026  
**Ambiente**: Homologação  
**VM**: 10.10.11.93 (gestor / Gjh!EDOl99$)  
**Domínio**: apoioarquivisticohml.oais.cloud  
**HTTP**: Sim (sem HTTPS)  

---

## 📋 Pré-requisitos Checklist

- [x] SSH client instalado no Windows (Windows 10+)
- [x] Conectividade de rede com 10.10.11.93
- [x] Usuário `gestor` com senha `Gjh!EDOl99$`
- [x] Docker + Docker Compose instalados na VM
- [x] `/opt/gestao_de_apoio_arquivistico_hml` existe no servidor
- [x] `postgres_data_hml` volume existe (NÃO remover!)

---

## 🔧 Opção 1: Deploy Automático (Recomendado)

### PowerShell (Windows 10+)

```powershell
# 1. Abra PowerShell e vá ao diretório do projeto
cd c:\des\gestao_de_apoio_arquivistico

# 2. Teste SSH connectivity
ssh -o ConnectTimeout=5 gestor@10.10.11.93 "echo 'OK'"
# Se falhar, veja "Troubleshooting SSH" abaixo

# 3. Execute o deploy automático
powershell -ExecutionPolicy Bypass -File deploy_homolog_auto.ps1

# Aguarde ~5-10 minutos para conclusão
```

**O que o script faz automaticamente**:
- ✅ Git pull main (local)
- ✅ Copia script para VM via SCP
- ✅ Executa deploy remoto (com sudo)
- ✅ Alembic upgrade head
- ✅ Validação de healthcheck
- ✅ Listagem de containers

---

## 🔧 Opção 2: Deploy Manual (Passo a Passo)

### Passo 1: Atualizar Git Localmente

```bash
# PowerShell
cd c:\des\gestao_de_apoio_arquivistico
git fetch origin main
git checkout main
git pull --ff-only origin main
```

**Esperado**: `Your branch is up to date with 'origin/main'`

---

### Passo 2: Conectar SSH na VM

```bash
# PowerShell
ssh gestor@10.10.11.93

# Será solicitada senha: Gjh!EDOl99$
```

**Você deve estar agora no shell da VM**:
```
gestor@srv-hml:~$
```

---

### Passo 3: Navegar para o App Directory

```bash
# Na VM
cd /opt/gestao_de_apoio_arquivistico_hml
pwd  # Deve retornar: /opt/gestao_de_apoio_arquivistico_hml
```

---

### Passo 4: Atualizar Git na VM

```bash
# Na VM
git fetch origin main
git checkout main
git pull --ff-only origin main

# Esperado: "Your branch is up to date with 'origin/main'"
```

---

### Passo 5: Preparar .env.homolog

```bash
# Na VM
# Verificar se .env.homolog existe
ls -la .env.homolog

# Se NÃO existir, criar:
sudo bash deploy/oci/remote_prepare_env_hml.sh
# Isso gera .env.homolog com valores automáticos

# Se JÁ EXISTE, preservar as credenciais:
cat .env.homolog | head -20
```

**Validar que o arquivo contém**:
```
NEXT_PUBLIC_API_URL=http://apoioarquivisticohml.oais.cloud/api/v1
POSTGRES_PASSWORD=<algo_setado>
REDIS_PASSWORD=<algo_setado>
ENVIRONMENT=homolog
```

---

### Passo 6: Validar .env.homolog (SEM CHANGE_ME)

```bash
# Na VM
grep "CHANGE_ME" .env.homolog
# Não deve retornar nada (exit code 1)

# Se retornar CHANGE_ME:
nano .env.homolog
# Editar manualmente os valores
```

---

### Passo 7: Docker Compose Build

```bash
# Na VM
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  build

# Esperado: "Successfully tagged gaa-backend:homolog" e "gaa-frontend:homolog"
# Tempo: ~5-10 minutos
```

---

### Passo 8: Docker Compose Up (SEM --volumes!)

```bash
# Na VM
# ⚠️ IMPORTANTE: NUNCA use --volumes
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  up -d --remove-orphans

# Esperado: 8 containers iniciados
```

**Verificar containers**:
```bash
docker compose -f docker-compose.homolog.yml ps

# Esperado:
# hml-postgres         Up (healthy)
# hml-redis            Up (healthy)
# hml-minio            Up
# hml-backend          Up (starting...)
# hml-celery-worker    Up
# hml-celery-beat      Up
# hml-frontend         Up
# hml-nginx            Up
```

---

### Passo 9: Aguardar PostgreSQL

```bash
# Na VM
# Aguardar ~30 segundos para PostgreSQL estar pronto
for i in {1..30}; do
  if docker compose -f docker-compose.homolog.yml \
      --env-file .env.homolog \
      exec -T postgres pg_isready -U gestor_hml >/dev/null 2>&1; then
    echo "[✓] PostgreSQL pronto!"
    break
  fi
  echo -n "."
  sleep 1
done
```

---

### Passo 10: Executar Alembic Upgrade Head

```bash
# Na VM
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  exec -T backend alembic upgrade head

# Esperado:
# INFO  [alembic.migration] Context impl PostgresqlImpl.
# INFO  [alembic.migration] Will assume transactional DDL.
# INFO  [alembic.migration] Running upgrade ...
# (pode ter múltiplas migrações)
# INFO  [alembic.migration] Done.
```

---

### Passo 11: Aguardar Backend Health

```bash
# Na VM
# Aguardar ~30 segundos
for i in {1..30}; do
  if docker compose -f docker-compose.homolog.yml \
      --env-file .env.homolog \
      exec -T backend curl -fs http://localhost:8000/health >/dev/null 2>&1; then
    echo "[✓] Backend pronto!"
    break
  fi
  echo -n "."
  sleep 2
done
```

---

### Passo 12: Reiniciar Nginx

```bash
# Na VM
# (Importante: atualizar upstreams DNS/IP após recrear backend)
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  restart hml-nginx

# Aguardar ~5 segundos
sleep 5
```

---

### Passo 13: Validar Healthcheck

```bash
# Na VM (ainda conectado via SSH)
curl -v http://127.0.0.1:8080/health

# Esperado (HTTP 200):
# {
#   "status": "ok",
#   "service": "gestao-arquivistica",
#   "version": "0.1.0",
#   "environment": "homolog"
# }
```

---

### Passo 14: Validar Frontend

```bash
# Na VM
curl -s -I http://127.0.0.1:8080/ | head -1

# Esperado: HTTP/1.1 200 OK
```

---

### Passo 15: Validar Swagger

```bash
# Na VM
curl -s -I http://127.0.0.1:8080/docs | head -1

# Esperado: HTTP/1.1 200 OK
```

---

## ✅ CHECKLIST FINAL

Copie e cole este checklist para validar:

```bash
# All checks in one (execute from VM):

echo "════════════════════════════════════════"
echo "CHECKLIST FINAL DE VALIDAÇÃO"
echo "════════════════════════════════════════"
echo ""

echo "[1] Containers running:"
docker compose -f docker-compose.homolog.yml --env-file .env.homolog ps --no-trunc | grep -E "hml-(postgres|redis|minio|backend|celery|frontend|nginx)" | wc -l
echo "    ✓ Esperado: 8 containers"
echo ""

echo "[2] PostgreSQL health:"
docker compose -f docker-compose.homolog.yml --env-file .env.homolog exec -T postgres pg_isready -U gestor_hml && echo "    ✓ OK" || echo "    ✗ FALHA"
echo ""

echo "[3] Backend health:"
curl -s http://127.0.0.1:8080/health | head -c 100 && echo "" && echo "    ✓ OK" || echo "    ✗ FALHA"
echo ""

echo "[4] Frontend OK:"
curl -s -I http://127.0.0.1:8080/ | head -1 && echo "    ✓ OK" || echo "    ✗ FALHA"
echo ""

echo "[5] Swagger OK:"
curl -s -I http://127.0.0.1:8080/docs | head -1 && echo "    ✓ OK" || echo "    ✗ FALHA"
echo ""

echo "[6] Alembic current version:"
docker compose -f docker-compose.homolog.yml --env-file .env.homolog exec -T backend alembic current
echo ""

echo "[7] .env.homolog sem CHANGE_ME:"
! grep "CHANGE_ME" .env.homolog && echo "    ✓ OK" || echo "    ✗ FALHA"
echo ""

echo "════════════════════════════════════════"
echo "SE TODOS OS ITENS TIVEREM ✓ = SUCESSO!"
echo "════════════════════════════════════════"
```

---

## 🚨 Troubleshooting

### SSH Connection Failed

```bash
# Verificar conectividade de rede
ping 10.10.11.93

# Se falhar: verifique firewall/rede interna

# Testar SSH sem password (com agent forwarding)
ssh -v gestor@10.10.11.93

# Se pedir password, use:
ssh -o PubkeyAuthentication=no gestor@10.10.11.93
```

### Backend não inicia

```bash
# Na VM, verificar logs
docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  logs --tail=50 hml-backend

# Procurar por erros de:
# - POSTGRES_PASSWORD incorreta
# - DATABASE_URL incorreta
# - PORT já em uso
```

### Nginx retorna 502

```bash
# Na VM - verificar se backend está health
curl http://127.0.0.1:8000/health

# Se falhar, reiniciar backend
docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  restart hml-backend

# Aguardar 10s
sleep 10

# Reiniciar nginx
docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  restart hml-nginx
```

### Banco não conecta

```bash
# Na VM - verificar volume
docker volume ls | grep hml

# Verificar container
docker compose -f docker-compose.homolog.yml ps hml-postgres

# Se container houver saído, ver logs
docker logs hml-postgres | tail -20
```

### Alembic falha

```bash
# Na VM - ver current version
docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  exec -T backend alembic current

# Ver história
docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  exec -T backend alembic history --verbose | head -20
```

---

## 🔒 Lembrete de Segurança

**NUNCA FAZER**:
- ❌ `docker compose down --volumes` (apagaria `postgres_data_hml`)
- ❌ `docker volume rm postgres_data_hml` (perda irrecuperável de dados)
- ❌ `alembic downgrade` (em env com dados)
- ❌ Regenerar `POSTGRES_PASSWORD` sem `ALTER USER` no banco
- ❌ Expor HTTP porta 80 publicamente (apenas via SSH tunnel)

**SEMPRE FIZER**:
- ✅ Usar `docker compose up -d` (SEM `--volumes`)
- ✅ Apenas `alembic upgrade head`
- ✅ Backup de `postgres_data_hml` antes de ops destrutivas
- ✅ Usar SSH tunnel para acesso remoto
- ✅ Preservar credenciais em `.env.homolog`

---

## 📞 Próximas Etapas

### Acessar Homologação via SSH Tunnel

```bash
# PowerShell (Windows)
ssh -L 8080:127.0.0.1:8080 gestor@10.10.11.93

# Deixar terminal aberto

# Em outro PowerShell, acesse:
# - Frontend: http://localhost:8080/
# - Swagger: http://localhost:8080/docs
# - ReDoc: http://localhost:8080/redoc
# - Healthcheck: http://localhost:8080/health
```

### Monitorar Logs em Tempo Real

```bash
# SSH na VM
ssh gestor@10.10.11.93

# Depois:
cd /opt/gestao_de_apoio_arquivistico_hml
docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  logs -f hml-backend
```

### Testar API

```bash
# Curl via SSH tunnel (PowerShell local):
curl http://localhost:8080/api/v1/health
curl http://localhost:8080/docs
```

---

## ✨ Sucesso!

Se chegou até aqui, **DEPLOY CONCLUÍDO COM SUCESSO!** 🎉

**Próxima ação**: Acessar via SSH tunnel e validar manualmente.

---

**Timestamp**: 2026-03-23 00:00:00 UTC  
**Documentação**: `/opt/gestao_de_apoio_arquivistico_hml/docs/LOCAL_DEV.md`
