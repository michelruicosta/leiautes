# Pendências — Leiautes Bacen

**Atualizado:** 2026-09-18 20:30
**Regra:** este arquivo lista **só o que ainda falta**. O que já foi feito está em `REGISTRO_CORRECOES.md`.

Checklist antigo de fases (não usar como “onde paramos”): `documentacao/CHECKLIST_IMPLEMENTACAO.md`.

Origem dos itens A01-x: auditoria OWASP A01 (controle de acesso) de 18/09/2026 — resumo no `REGISTRO_CORRECOES.md`.

---

## 🔴 URGENTE

- **A01-1/2/4/5/8/9/11/13 — Publicar no servidor.** Tudo corrigido e verificado neste PC em 18/09. **O site no ar está desatualizado até publicar.** Passos: `git push` → VPS: `git pull && systemctl restart leiautes_bacen-api` → adicionar ao `.env` de produção: `ENVIRONMENT=production` e `CORS_ALLOW_ORIGINS=https://finaudapps.com.br,https://www.finaudapps.com.br,https://admin.finaudapps.com.br,https://leiautes-bacen.finaudapps.com.br,https://www.leiautes-bacen.finaudapps.com.br`. Depois conferir: `/api/dashboard` sem login = 401; SSO continua entrando; `/api/docs` = 404; `/api/auth/login` = 404; auditoria mostra e-mail real de quem editou.

---

## 🟡 DESTE APP

- **A01-3 — ~~Login/recuperação sem rate limiting~~** — resolvido pela remoção do login local. O `/auth/logout` que resta não justifica rate limiting.
- **A01-4 ✅** — resolvido em 18/09 (usuário inativo nega acesso pelo SSO).
- **A01-5 ✅** — resolvido em 18/09 (operador não tem mais `admin-robo` por padrão; migração automática no startup).
- **A01-6 — Sessão SSO não pode ser cancelada pelo servidor.** A sessão é gerenciada pelo portal; este app só apaga o cookie local no logout. Se o portal não tiver revogação, uma sessão copiada pode persistir. **Decisão no projeto do portal.**
- **A01-7 — Nenhum security header em produção** (HSTS, X-Frame-Options, nosniff, CSP, Referrer-Policy) e `x-powered-by: CyberPanel-OLS` exposto. Feito no vHost/Cloudflare, não no código.
- **A01-8 ✅** — resolvido em 18/09 (registrar_log passa `usuario["email"]` em todos os routers).
- **A01-9 ✅** — resolvido em 18/09 (`ENVIRONMENT=production` desliga /docs e /openapi.json).
- **A01-10 —** `AUTH_SECRET_KEY` removida da config junto com o login local; `AUTH_SEED_PASSWORD` também removida. ✅ Resolvido como efeito colateral da remoção do login.
- **A01-11 ✅** — resolvido pela remoção do endpoint de login.
- **A01-12 —** Sem trava contra excluir a si mesmo / o último administrador; `PUT /usuarios/perfis/permissoes` aceita qualquer nome de perfil/rota.
- **A01-13 ✅** — resolvido em 18/09 (CORS vem de `CORS_ALLOW_ORIGINS` no `.env`).
- **A01-14 —** Download de versões e leitura de log sem cerca de pasta — restringir a `storage/` e `logs/`.
- **Ambiente de teste:** o `TestClient` do FastAPI neste venv pede um pacote `httpx2` que não está instalado. Não foi instalado (pacote não conferido). Verificar a origem antes de decidir.

---

## 🔵 OUTRO PROJETO / DEPOIS

- **A01-5 / A01-4 (lado do portal):** conferir se o portal consegue informar quais apps cada usuário tem liberados — depende do projeto do portal.
