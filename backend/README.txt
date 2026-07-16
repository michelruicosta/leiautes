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

## Observacoes

- A API inicializa o banco SQLite em `dados/leiautes.db`.
- As tabelas iniciais contemplam configuracoes, leiautes monitorados,
  execucoes, arquivos, versoes, alteracoes, e-mails enviados e auditoria.
- O motor atual em `scripts/verifica_leiautes_finaud.py` ainda nao foi migrado;
  a migracao sera feita em etapa propria do checklist.
