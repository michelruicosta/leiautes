# Pendências — Leiautes Bacen

**Atualizado:** 2026-09-19 00:30
**Regra:** este arquivo lista **só o que ainda falta**. O que já foi feito está em `REGISTRO_CORRECOES.md`.

Checklist antigo de fases (não usar como “onde paramos”): `documentacao/CHECKLIST_IMPLEMENTACAO.md`.

Origem dos itens A01-x: auditoria OWASP A01 (controle de acesso) de 18/09/2026 — resumo no `REGISTRO_CORRECOES.md`.

---

## 🔴 URGENTE

- **A01 — Fechar a conferência da publicação (só no navegador).** Publicado na VPS em 18/09 22:43 e conferido de fora (401/404 certos, commit `9ea0bf6`, `.env` com as duas variáveis). **Falta:** Michel entrar pelo portal SSO e fazer uma edição pequena em Administração; depois conferir que a auditoria grava o e-mail real (não `gestor@finaud.com.br`). Até 18/09 23:40 ninguém tinha entrado desde o restart.

- **Publicar o frontend sem a tela de senha.** Corrigido neste PC em 19/09 (ver REGISTRO). O site no ar ainda mostra e-mail/senha e responde "Not Found" ao tentar entrar. Falta: push + gerar o `dist` na VPS (o `dist` de lá é de 31/08) e conferir no navegador.

---

## 🟡 DESTE APP

- **Sobra de senha local em Usuários e perfis.** A tela (`frontend/src/pages/UsuariosPage.tsx`, opção "definir senha no app") e o backend (`backend/app/routers/usuarios.py`: `senha_inicial` / `nova_senha`) ainda gravam senha local, que não serve mais para nada desde a remoção do login em 18/09. Remover dos dois lados e decidir o que fazer com a coluna `senha_hash`.

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
