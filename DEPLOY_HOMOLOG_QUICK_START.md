# ✅ DEPLOY HOMOLOGAÇÃO — GUIA RÁPIDO FINAL

**Status**: ✨ **PRONTO PARA EXECUÇÃO**  
**Data**: 23 de março de 2026  
**Ambiente**: Homologação  
**VM**: 10.10.11.93 (gestor / Gjh!EDOl99$)  
**Domínio**: `apoioarquivisticohml.oais.cloud`  

---

## 🚀 EXECUTE AGORA (Opção Recomendada)

### Usando Git Bash / WSL / Terminal Linux

```bash
# 1. Abra Git Bash OU WSL (Windows)
# 2. Navegue até o projeto
cd /mnt/c/des/gestao_de_apoio_arquivistico  # WSL
# OU
cd /c/des/gestao_de_apoio_arquivistico      # Git Bash

# 3. Execute o script de deploy
bash ./deploy_homolog_execute.sh
```

**O script faz automaticamente**:
- ✅ Git atualiza `main` (local e remoto)
- ✅ Copia `deploy_homolog_safe.sh` para a VM
- ✅ Executa deploy remoto com `sudo`
- ✅ Alembic `upgrade head`
- ✅ Docker Compose `up -d` (SEM `--volumes`)
- ✅ Valida healthcheck
- ✅ Lista containers

**Tempo**: ~10-15 minutos

---

## 🔧 SE Preferir Manualmente (Via SSH)

### Terminal (qualquer shell com SSH)

```bash
# 1. Connect SSH
ssh gestor@10.10.11.93
# Digite a senha: Gjh!EDOl99$

# 2. Entrar no diretório
cd /opt/gestao_de_apoio_arquivistico_hml

# 3. Atualizar git
git fetch origin main && git checkout main && git pull --ff-only origin main

# 4. Validar .env.homolog (se NÃO existe, criar)
if [ ! -f .env.homolog ]; then
  sudo bash deploy/oci/remote_prepare_env_hml.sh
fi

# 5. Validar sem CHANGE_ME
grep CHANGE_ME .env.homolog && echo "❌ FALHA" || echo "✅ OK"

# 6. Build
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  build

# 7. UP (SEM --volumes!)
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  up -d --remove-orphans

# 8. Aguardar PostgreSQL
for i in {1..30}; do
  if docker compose -f docker-compose.homolog.yml \
      --env-file .env.homolog \
      exec -T postgres pg_isready -U gestor_hml >/dev/null 2>&1; then
    echo "✅ PostgreSQL pronto"
    break
  fi
  echo -n "."
  sleep 1
done

# 9. Alembic upgrade
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  exec -T backend alembic upgrade head

# 10. Reiniciar Nginx (atualizar upstreams)
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  restart hml-nginx

# 11. Validar healthcheck
sleep 5
curl -v http://127.0.0.1:8080/health
# Esperado: HTTP 200 com status "ok"

# 12. Verificar containers
docker compose -f docker-compose.homolog.yml ps
```

---

## ✅ VALIDAÇÃO FINAL

Após deploy, copie e execute este checklist:

```bash
# SSH na VM
ssh gestor@10.10.11.93
cd /opt/gestao_de_apoio_arquivistico_hml

# Validar cada item
echo "1. Containers:" && \
docker compose -f docker-compose.homolog.yml --env-file .env.homolog ps --no-trunc | grep -c "Up" && \
echo "   (deve retornar 8 ou mais)"

echo "2. PostgreSQL:" && \
docker compose -f docker-compose.homolog.yml --env-file .env.homolog \
  exec -T postgres pg_isready -U gestor_hml && \
echo "   ✅ OK"

echo "3. Backend health:" && \
curl -s http://127.0.0.1:8080/health | jq '.status' && \
echo "   (deve retornar \"ok\")"

echo "4. Frontend:" && \
curl -s -I http://127.0.0.1:8080/ | head -1 && \
echo "   (deve retornar HTTP/1.1 200 OK)"

echo "5. Swagger:" && \
curl -s -I http://127.0.0.1:8080/docs | head -1 && \
echo "   (deve retornar HTTP/1.1 200 OK)"

echo "6. DB tables:" && \
docker compose -f docker-compose.homolog.yml --env-file .env.homolog \
  exec -T postgres psql -U gestor_hml -d gestao_arquivistica_hml -c "\\dt" && \
echo "   (deve listar as tabelas)"

echo "════════════════════════════════════════════════════════════"
echo "SE TODOS OS ITENS RETORNAREM OK = SUCESSO! 🎉"
echo "════════════════════════════════════════════════════════════"
```

---

## 📊 Acessar Homologação Remotamente

### Via SSH Tunnel (Recomendado)

```bash
# Abrir SSH tunnel em um terminal
ssh -L 8080:127.0.0.1:8080 gestor@10.10.11.93

# Em outro terminal/navegador OU dentro do VS Code
# Acesse:
# - Frontend: http://localhost:8080/
# - Swagger: http://localhost:8080/docs
# - ReDoc: http://localhost:8080/redoc
# - Healthcheck: http://localhost:8080/health
```

### Monitorar Logs em Tempo Real

```bash
ssh gestor@10.10.11.93
cd /opt/gestao_de_apoio_arquivistico_hml

# Backend logs
docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  logs -f hml-backend

# Ou todos os containers
docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  logs -f
```

---

## 🚨 Se der Erro

### Backend não inicia

```bash
# Ver logs
docker compose -f docker-compose.homolog.yml logs hml-backend | tail -50

# Procurar por:
# - ERROR: database connection
# - ERROR: redis connection
# - ERROR in config
```

### Nginx 502 Bad Gateway

```bash
# Backend está vivo?
curl http://127.0.0.1:8000/health

# Se falhar ou timeout, reiniciar backend
docker compose -f docker-compose.homolog.yml restart hml-backend

# Aguardar 10s
sleep 10

# Reiniciar Nginx
docker compose -f docker-compose.homolog.yml restart hml-nginx
```

### Banco não conecta

```bash
# Verificar volume
docker volume ls | grep hml

# Verificar container
docker logs hml-postgres | tail -20

# Se container saiu, verificar status
docker ps -a | grep hml-postgres
```

### Alembic falha

```bash
# Ver current version
docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  exec -T backend alembic current

# Ver histórico
docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  exec -T backend alembic history -v | head -20
```

---

## 🔒 Restrições Críticas

**❌ NUNCA EXECUTAR**:
- `docker compose down --volumes` (apagaria `postgres_data_hml`)
- `docker volume rm postgres_data_hml` (perda irreversível)
- `alembic downgrade` (quebra migrações)
- Regenerar POSTGRES_PASSWORD sem `ALTER USER` no banco
- Expor HTTP porta 80 publicamente (usar SSH tunnel)

**✅ SEMPRE FAZER**:
- `docker compose up -d` (sem `--volumes`)
- Apenas `alembic upgrade head`
- Backup de `postgres_data_hml` antes de ops destrutivas
- SSH tunnel para acesso remoto
- Preservar credenciais em `.env.homolog`

---

## 📝 Checklist de Atualização (Próximas Vezes)

Para futuras atualizações, rápido:

```bash
ssh gestor@10.10.11.93
cd /opt/gestao_de_apoio_arquivistico_hml

# 1. Atualizar código
git pull origin main

# 2. Build apenas o backend/frontend alterado
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  build backend frontend

# 3. Subir (sem --volumes!)
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  up -d --remove-orphans

# 4. Se houver novas migrações
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  exec -T backend alembic upgrade head

# 5. Reiniciar Nginx
sudo docker compose -f docker-compose.homolog.yml \
  --env-file .env.homolog \
  restart hml-nginx

# 6. Validar
curl http://127.0.0.1:8080/health
```

---

## 🎯 Status Final

```
✅ Scripts de deploy preparados:
   - deploy_homolog_execute.sh (recomendado)
   - deploy_homolog_auto.ps1 (Windows com PowerShell)
   - deploy/oci/deploy_homolog_safe.sh (core remoto)

✅ Documentação completa:
   - DEPLOY_HOMOLOG_CHECKLIST.md
   - DEPLOY_HOMOLOG_MANUAL.md
   - Este arquivo

✅ Configuração validada:
   - Domínio: apoioarquivisticohml.oais.cloud
   - API URL: http://apoioarquivisticohml.oais.cloud/api/v1
   - HTTP (sem HTTPS) ✓
   - postgres_data_hml preservado ✓
   - Nginx reiniciado após backend ✓

🚀 NEXT: Execute ./deploy_homolog_execute.sh via Git Bash/WSL
```

---

**Última Atualização**: 2026-03-23 00:00:00 UTC  
**Responsabilidade**: Gestor de Homologação  
**Contato**: Documentação em `/opt/gestao_de_apoio_arquivistico_hml/docs/`
