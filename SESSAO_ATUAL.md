# Sessão atual — Leiautes Bacen

| Campo | Valor |
|-------|-------|
| **Última atualização** | 2026-09-18 20:45 |
| **Branch ativa** | `main` |
| **Estado geral** | Site no ar. Auditoria OWASP A01 concluída. 8 achados corrigidos e em produção pendente de publicação na VPS. |

---

## Estado atual

- **Site:** `https://leiautes-bacen.finaudapps.com.br`
- **Caderno git:** `main` — commit `9ea0bf6` já no GitHub, **aguardando `git pull` + restart na VPS**
- **Neste PC:** tela **5177** · API **8003**
- **Login:** exclusivamente SSO do portal Finaud (login local removido em 18/09)

---

## 🔥 Próximo assunto

**Publicar na VPS** — o commit de segurança está no GitHub mas o site no ar ainda tem o código antigo:

```bash
cd /srv/finaud/tec/leiautes_bacen
git pull
# adicionar ao .env:
# ENVIRONMENT=production
# CORS_ALLOW_ORIGINS=https://finaudapps.com.br,https://www.finaudapps.com.br,https://admin.finaudapps.com.br,https://leiautes-bacen.finaudapps.com.br,https://www.leiautes-bacen.finaudapps.com.br
systemctl restart leiautes_bacen-api
```

Conferir após restart: `/api/dashboard` sem login → **401** · `/api/docs` → **404** · SSO continua entrando.

---

## Regras em vigor

- Nunca commitar `.env` nem credenciais
- Não push sem OK explícito
- Trabalho só na `main`. Não criar ramo novo
- Neste app **não pode ter Perfil**; acesso só pelo portal SSO (login local removido em 18/09)
- Cadastro de leiautes só em **Administração**
- Estado deste projeto só no bordo deste repo (não no mapa geral)

---

## Histórico recente

Detalhe de cada conserto: `documentações/REGISTRO_CORRECOES.md`. O que ainda falta: `documentações/PENDENCIAS.md`.

| Data | Tema |
|------|------|
| 18/09 | Auditoria OWASP A01 + 8 achados corrigidos (login local removido, 5 rotas protegidas, CORS, docs, auditoria) |
| 01/09 | Cadernos de bordo no molde do Normativos |
| 01/09 | Chamado de senha/Perfil conferido e arquivado |
| 27/08 | Senha só no portal (sem Perfil / Esqueceu a senha) |
| 27/08 | Cadastro de Leiautes na Administração |
| 24/08 | Robô novo no ar; MCC e DRSAC 2030 |
