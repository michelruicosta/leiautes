# Leiautes — SSO portal (deploy)

Ver padrão completo: `Projeto_Auditoria_IA/documentacao/sso_portal_apps_finaud.md`

## .env produção (VPS)

```env
AUTH_COOKIE_DOMAIN=.finaudapps.com.br
PORTAL_AUTH_URL=http://127.0.0.1:8000
PORTAL_AUTH_LEGACY_URL=http://127.0.0.1:8002
PORTAL_URL=https://finaudapps.com.br
```

## Deploy

```bash
cd /srv/finaud/leiautes   # ajustar caminho real
git pull origin main
systemctl restart leiautes_bacen-api
```

## Teste

1. Login em `finaudapps.com.br`
2. Abrir card **Leiautes IA**
3. Deve entrar sem tela de login (se o e-mail existir em Usuários do Leiautes)

## Cadastro

Michel (ou admin) precisa existir na tela **Usuários** do Leiautes com o **mesmo e-mail** do portal.
