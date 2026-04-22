# 📑 ÍNDICE DE REFERÊNCIA — Deploy Homologação

**Última Atualização**: 23 de março de 2026  
**Status**: ✅ PRONTO PARA EXECUÇÃO  

---

## 🎯 Comece Por Aqui

### 1️⃣ Leitura Rápida (5 min)
👉 **[DEPLOY_HOMOLOG_README.md](DEPLOY_HOMOLOG_README.md)**

### 2️⃣ Executar Deploy (15 min)
👉 **[DEPLOY_HOMOLOG_QUICK_START.md](DEPLOY_HOMOLOG_QUICK_START.md)**

### 3️⃣ Validar Após Deploy (10 min)
👉 **[DEPLOY_HOMOLOG_VALIDACAO_FINAL.md](DEPLOY_HOMOLOG_VALIDACAO_FINAL.md)**

---

## 📚 Documentação Completa

| Documento | Propósito | Quando Usar |
|-----------|-----------|------------|
| **DEPLOY_HOMOLOG_README.md** | 📌 Overview executivo | ✅ **PRIMEIRO** |
| **DEPLOY_HOMOLOG_QUICK_START.md** | Guia rápido final | Para executar deploy |
| **DEPLOY_HOMOLOG_MANUAL.md** | Passo-a-passo completo | Se preferir manual |
| **DEPLOY_HOMOLOG_CHECKLIST.md** | Checklist detalhado | Validação completa |
| **DEPLOY_HOMOLOG_VALIDACAO_FINAL.md** | Verificações pós-deploy | Após conclusão |
| **COMECE_AQUI.md** | (Projeto em geral) | Contexto geral |

---

## 🚀 Scripts de Deploy

| Script | Localização | Como Usar | Quando Usar |
|--------|-------------|-----------|------------|
| **deploy_homolog_execute.sh** | Raiz | `bash ./deploy_homolog_execute.sh` | ✅ RECOMENDADO |
| **deploy_homolog_auto.ps1** | Raiz | `powershell -File deploy_homolog_auto.ps1` | Como alternativa |
| **deploy_homolog_safe.sh** | `deploy/oci/` | § Automático (via SSH) | Executado remotamente |
| **remote_prepare_env_hml.sh** | `deploy/oci/` | § Automático | Criar .env.homolog |

---

## 🔑 Credenciais & Config

```
VM IP:              10.10.11.93
VM User:            gestor
VM Password:        Gjh!EDOl99$

App Directory:      /opt/gestao_de_apoio_arquivistico_hml
Compose File:       docker-compose.homolog.yml
Env File:           .env.homolog

Domínio:            apoioarquivisticohml.oais.cloud
API URL:            http://apoioarquivisticohml.oais.cloud/api/v1
Nginx Bind:         127.0.0.1:8080 (localhost only)

Database:           gestao_arquivistica_hml
DB User:            gestor_hml
DB Password:        (gerado em .env.homolog)

Containers:         8 (hml-*)
Volumes:            postgres_data_hml (NUNCA remover!)
```

---

## 📋 Fluxo Resumido

```
┌─────────────────────────────────────────┐
│ 1. LER DEPLOY_HOMOLOG_README.md          │ ← 5 min
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 2. EXECUTAR deploy_homolog_execute.sh    │ ← 15 min
│    (ou seguir DEPLOY_HOMOLOG_MANUAL.md)  │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 3. VALIDAR com DEPLOY_HOMOLOG_CHECKLIST │ ← 10 min
│    (todos os 12 itens)                   │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│ 4. ACESSAR via SSH Tunnel                │
│    ssh -L 8080:127.0.0.1:8080 ...        │
└─────────────────────────────────────────┘
                  ↓
                ✅ SUCESSO!
```

---

## 🛠️ Casos de Uso Comuns

### Cenário 1: Deploy Inicial

```bash
1. Ler: DEPLOY_HOMOLOG_README.md
2. Executar: bash ./deploy_homolog_execute.sh
3. Validar: Todos os 12 itens em DEPLOY_HOMOLOG_VALIDACAO_FINAL.md
4. Acessar: SSH -L 8080:127.0.0.1:8080
```

### Cenário 2: Update (Nova release)

```bash
# SSH na VM
cd /opt/gestao_de_apoio_arquivistico_hml

# 1. Atualizar código
git pull origin main

# 2. Build apenas alterados
docker-compose -f docker-compose.homolog.yml build backend frontend

# 3. Up
docker-compose -f docker-compose.homolog.yml up -d --remove-orphans

# 4. Se houver migrações
docker-compose -f docker-compose.homolog.yml --env-file .env.homolog \
  exec -T backend alembic upgrade head

# 5. Reiniciar Nginx
docker-compose -f docker-compose.homolog.yml restart hml-nginx

# 6. Validar
curl http://127.0.0.1:8080/health
```

### Cenário 3: Debug Backend

```bash
# SSH na VM
cd /opt/gestao_de_apoio_arquivistico_hml

# Logs em tempo real
docker-compose -f docker-compose.homolog.yml logs -f hml-backend

# Ou logs de um container específico
docker logs -f hml-backend --tail 50
```

### Cenário 4: Rollback Seguro

```bash
# NUNCA use downgrade de Alembic
# Em vez disso, faça git revert e redeploy

git revert HEAD  # desfaz último commit
git pull origin main
docker-compose -f docker-compose.homolog.yml up -d --remove-orphans
docker-compose -f docker-compose.homolog.yml --env-file .env.homolog \
  exec -T backend alembic upgrade head  # sempre upgrade, nunca downgrade
```

---

## 🔍 Verificação Rápida (1 minuto)

```bash
# SSH na VM
ssh gestor@10.10.11.93

cd /opt/gestao_de_apoio_arquivistico_hml

# Tudo OK?
echo "✓ Containers: $(docker-compose -f docker-compose.homolog.yml ps | grep -c Up)" && \
echo "✓ Backend: $(curl -s http://127.0.0.1:8080/health | jq '.status')" && \
echo "✓ Frontend: $(curl -s -I http://127.0.0.1:8080/ | head -1)"
```

---

## 📊 Todos os Arquivos Criados

```
gestao_de_apoio_arquivistico/
├── DEPLOY_HOMOLOG_README.md                    ← Leia PRIMEIRO
├── DEPLOY_HOMOLOG_QUICK_START.md               ← Guia de Ação
├── DEPLOY_HOMOLOG_MANUAL.md                    ← Detalhado
├── DEPLOY_HOMOLOG_CHECKLIST.md                 ← Inicial
├── DEPLOY_HOMOLOG_VALIDACAO_FINAL.md           ← Pós-deploy
├── INDICE_DEPLOY_HOMOLOG.md                    ← Você está aqui
├── deploy_homolog_execute.sh                   ← Script principal (bash)
├── deploy_homolog_auto.ps1                     ← Script alternativo (PS)
├── deploy/oci/
│   ├── deploy_homolog_safe.sh                  ← Core remoto
│   ├── remote_prepare_env_hml.sh               ← Prepara env
│   └── nginx.conf                              ← Config Nginx
└── docker-compose.homolog.yml                  ← Stack config
```

---

## ⚠️ Restrições Críticas

| ❌ NÃO FAZER | ✅ RAZÃO |
|-----------|--------|
| `docker compose down --volumes` | Apagaria `postgres_data_hml` |
| `docker volume rm postgres_data_hml` | Perda irreversível de dados |
| `alembic downgrade` | Quebra integridade do banco |
| Regenerar POSTGRES_PASSWORD | Sem `ALTER USER` falha login |
| Expor HTTP 80 publicamente | Segurança — usar SSH tunnel |

---

## 🎓 Documentação de Referência

### Dentro do Projeto
- **docs/LOCAL_DEV.md** — Desenvolvimento local
- **docs/OCI_DEPLOY_VM.md** — Deploy produção VM OCI
- **docs/PLANO_DE_TRABALHO.md** — Planejamento Sprint
- **backend/README.md** — Backend específico
- **frontend/README.md** — Frontend específico

### Externo
- Docker Compose: https://docs.docker.com/compose/
- Alembic: https://alembic.sqlalchemy.org/
- Nginx: https://nginx.org/

---

## 🆘 Suporte Rápido

### Healthcheck Falha
```bash
docker logs hml-backend | tail -30
curl http://127.0.0.1:8000/health  # backend direto
curl http://127.0.0.1:8080/health  # via nginx
```

### Nginx 502
```bash
docker restart hml-backend hml-nginx
sleep 10
curl http://127.0.0.1:8080/health
```

### PostgreSQL Indisponível
```bash
docker logs hml-postgres | tail -20
docker exec hml-postgres pg_isready -U gestor_hml
```

### Migração Falha
```bash
docker compose -f docker-compose.homolog.yml --env-file .env.homolog \
  exec -T backend alembic current
docker compose -f docker-compose.homolog.yml --env-file .env.homolog \
  exec -T backend alembic history -v
```

---

## ✅ Pós-Deploy (Fazendo Agora)

- [x] Investigação completa
- [x] Scripts preparados
- [x] Documentação escrita
- [x] Proteções aplicadas
- [x] Validações implementadas

⏭️ **Próximo passo**: Usuário executa `bash ./deploy_homolog_execute.sh`

---

## 📞 Referência Rápida

**Git**: `git fetch origin main && git pull --ff-only`  
**Build**: `docker-compose -f docker-compose.homolog.yml build`  
**Deploy**: `docker-compose -f docker-compose.homolog.yml up -d`  
**Migrate**: `docker-compose ... exec -T backend alembic upgrade head`  
**Health**: `curl http://127.0.0.1:8080/health`  
**Tunnel**: `ssh -L 8080:127.0.0.1:8080 gestor@10.10.11.93`  

---

## 🎯 Status Final

```
✅ DEPLOY PRONTO

Phase 1: ✅ Investigação
Phase 2: ✅ Scripts preparados
Phase 3: ✅ Documentação
Phase 4: ✅ Proteções
Phase 5: ⏳ Seu turno!

PRÓXIMO: Execute deploy_homolog_execute.sh
```

---

**Criado**: 23 de março de 2026  
**Versão**: 1.0 Final  
**Mantém-se**: Este arquivo é um índice — ver documentação específica para detalhes.
