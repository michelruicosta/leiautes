# API Leiautes Bacen

Base FastAPI criada seguindo o padrao do projeto `normativos_ia`.

## Executar em desenvolvimento

Com o ambiente virtual ativo:

```bash
python -m pip install -r backend/requirements-api.txt
cd backend
python -m app.main
```

Endpoint inicial:

```text
GET /health
```

Endpoints iniciais para as telas:

```text
GET /dashboard
GET /leiautes
GET /alteracoes
GET /execucoes
GET /execucoes/ultima
GET /configuracoes
PUT /configuracoes
GET /robo/status
POST /robo/executar
GET /usuarios
GET /usuarios/perfis/permissoes
GET /email-gestor/preview
```

## Observacoes

- A API inicializa o banco SQLite em `dados/leiautes.db`.
- As tabelas iniciais contemplam configuracoes, leiautes monitorados,
  execucoes, arquivos, versoes, alteracoes, e-mails enviados e auditoria.
- A persistencia ja esta separada em modulos por dominio, seguindo a direcao
  usada no `normativos_ia`.
- A rota `/robo/executar` chama o motor atual em
  `scripts/verifica_leiautes_finaud.py` e registra a execucao no banco. A
  modularizacao interna do motor sera feita em etapa propria do checklist.
- Por seguranca, execucoes disparadas pela API definem
  `LEIAUTES_EMAIL_TEST_TO=michel@finaud.com.br`, redirecionando o envio para o
  e-mail de teste enquanto o app esta em desenvolvimento.
- A execucao pela API tambem aceita `enviar_email=false`; nesse caso define
  `LEIAUTES_DISABLE_EMAIL=1` e roda coleta/historico sem abrir SMTP.
