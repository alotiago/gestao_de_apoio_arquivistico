# ⚡ EXECUTE AGORA — Deploy Homologação

**Status**: ✅ Tudo pronto para ir ao ar!

---

## 🚀 1 Clique - Solução Completa

### Windows (Git Bash)

```bash
# Abra Git Bash aqui: c:\des\gestao_de_apoio_arquivistico 
# E execute:

bash ./deploy_homolog_execute.sh

# ↓ Será solicitada a senha do gestor: Gjh!EDOl99$
# ↓ Será solicitada a senha do sudo (mesma)
# ↓ Aguarde ~15 minutos
```

### Linux / macOS / WSL

```bash
cd /mnt/c/des/gestao_de_apoio_arquivistico  # WSL
# OU (direto no Linux)
cd ~/projects/gestao_de_apoio_arquivistico

bash ./deploy_homolog_execute.sh
```

---

## ✅ Se Tudo Correr Bem (Em 15-20 min)

```bash
# Você verá:
# ✓ Git atualizado em main
# ✓ Script copiado para VM via SCP
# ✓ Deploy remoto executado (alembic + docker-compose)
# ✓ Healthcheck validando OK
# ✓ 8 containers rodando

# Fim do script com:
# [✓] DEPLOY CONCLUÍDO COM SUCESSO!
```

---

## 🌐 Acessar (Após Conclusão)

### Opção 1: Via SSH Tunnel (Seguro)

```bash
# Terminal separado — abrir tunnel
ssh -L 8080:127.0.0.1:8080 gestor@10.10.11.93

# Depois acesse localmente:
http://localhost:8080/          # Frontend
http://localhost:8080/docs      # Swagger
http://localhost:8080/health    # Health
```

### Opção 2: Validação Rápida

```bash
ssh gestor@10.10.11.93

# Copiar e colar:
cd /opt/gestao_de_apoio_arquivistico_hml && \
echo "Containers: $(docker-compose -f docker-compose.homolog.yml ps | grep -c Up)" && \
echo "Health: $(curl -s http://127.0.0.1:8080/health | jq '.status')" && \
echo "Frontend: $(curl -s -I http://127.0.0.1:8080/ | head -1)"

# Esperado:
# Containers: 8
# Health: "ok"
# Frontend: HTTP/1.1 200 OK
```

---

## 📖 Documentação Referência

Se precisar de detalhes:

- **[DEPLOY_HOMOLOG_README.md](DEPLOY_HOMOLOG_README.md)** ← Overview
- **[DEPLOY_HOMOLOG_MANUAL.md](DEPLOY_HOMOLOG_MANUAL.md)** ← Passo-a-passo
- **[DEPLOY_HOMOLOG_VALIDACAO_FINAL.md](DEPLOY_HOMOLOG_VALIDACAO_FINAL.md)** ← Checklist
- **[INDICE_DEPLOY_HOMOLOG.md](INDICE_DEPLOY_HOMOLOG.md)** ← Índice

---

## 🎯 TL;DR (Muito Resumido)

```
1. bash ./deploy_homolog_execute.sh
2. Aguarde ~15 min
3. ssh -L 8080:127.0.0.1:8080 gestor@10.10.11.93
4. Acesse http://localhost:8080/
✅ Fim!
```

---

## 🚨 Se Algo Der Errado

```bash
# Verificar logs
ssh gestor@10.10.11.93
cd /opt/gestao_de_apoio_arquivistico_hml
docker-compose -f docker-compose.homolog.yml logs hml-backend | tail -50

# Ou ver [DEPLOY_HOMOLOG_MANUAL.md](DEPLOY_HOMOLOG_MANUAL.md) → Troubleshooting
```

---

**Próxima ação**: 
```bash
bash ./deploy_homolog_execute.sh
```

✨ Boa sorte!
