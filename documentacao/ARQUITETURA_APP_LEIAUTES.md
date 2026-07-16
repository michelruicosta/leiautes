# Arquitetura do App Leiautes Bacen

## Diretriz principal

O app Leiautes Bacen deve seguir a estrutura, arquitetura e padrao visual do projeto
`D:\02_Finaud\Projetos\concluidos\normativos_ia`.

O objetivo e evoluir o projeto atual, que hoje roda como script de monitoramento e
envio de e-mail, para um app com backend, frontend, login, configuracoes,
historico de execucoes e comparacao de versoes.

## Estrutura alvo

```text
leiautes/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── deps/
│   │   ├── models/
│   │   ├── routers/
│   │   └── services/
│   └── requirements-api.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── context/
│   │   ├── lib/
│   │   ├── pages/
│   │   └── styles/
│   ├── package.json
│   └── vite.config.ts
├── persistencia/
│   ├── db.py
│   ├── leiautes_db.py
│   ├── config_db.py
│   └── auditoria_db.py
├── dados/
│   └── app.sqlite3
├── storage/
│   └── arquivos/
├── logs/
├── scripts/
│   └── verifica_leiautes_finaud.py
└── run.sh
```

## Modulos principais

### Backend

Seguir FastAPI, como no `normativos_ia`.

Rotas previstas:

- `/health`: status da API.
- `/auth`: login, sessao, recuperacao de senha.
- `/dashboard`: resumo do monitoramento.
- `/leiautes`: cadastro e consulta dos leiautes monitorados.
- `/alteracoes`: historico e detalhe das diferencas.
- `/execucoes`: historico das execucoes do robo.
- `/robo`: executar manualmente, consultar agenda e status.
- `/configuracoes`: parametros que hoje estao fixos no script.
- `/usuarios`: gestao de usuarios, perfis e permissoes.

### Frontend

Seguir React + Vite + TypeScript, como no `normativos_ia`.

Menus previstos:

- Login
- Dashboard
- Leiautes
- Alteracoes
- E-mail do gestor
- Robo
- Configuracoes
- Usuarios e perfis

### Persistencia

Usar banco local SQLite no mesmo estilo do `normativos_ia`.

Entidades previstas:

- `usuarios`
- `perfis_permissoes`
- `configuracoes`
- `leiautes_monitorados`
- `execucoes`
- `arquivos_monitorados`
- `versoes_arquivos`
- `alteracoes_detectadas`
- `emails_enviados`
- `auditoria`

## Evolucao do script atual

O arquivo `scripts/verifica_leiautes_finaud.py` deve deixar de concentrar toda a
regra de negocio em um unico script. A regra sera quebrada em servicos:

- coleta das paginas Bacen;
- extracao de anexos;
- verificacao de metadados;
- download de versoes;
- comparacao de conteudo;
- registro da execucao;
- geracao de resumo;
- envio de e-mail.

O `run.sh` deve continuar existindo para compatibilidade operacional, mas passara
a chamar o motor novo.

## Comparacao de arquivos

Para informar ao gestor o que mudou, o app deve guardar historico de versoes.

Estrategia prevista:

- PDF: extrair texto e comparar trechos.
- XSD/XML: comparar estrutura e texto.
- XLS/XLSX: comparar abas, linhas, colunas e celulas.
- ZIP: registrar alteracao do pacote; comparacao interna pode entrar em fase posterior.

Cada alteracao deve gerar:

- resumo executivo;
- itens incluidos;
- itens removidos;
- itens alterados;
- impacto sugerido;
- link para detalhes no app.

## Parametrizacao

Tudo que hoje estiver hardcoded no script deve migrar para tela sempre que fizer
sentido operacional:

- URLs Bacen monitoradas;
- timeouts;
- filtros de pasta atual;
- padroes excluidos;
- limite de anexos;
- tamanho maximo de anexo;
- tamanho total do e-mail;
- envio sem alteracao;
- destinatarios;
- SMTP;
- assunto do e-mail;
- logo;
- caminho de logs;
- caminho de status publico;
- caminho do manifest;
- agenda do robo;
- feriados;
- criterios de comparacao;
- template do resumo para gestor.

## Regra de seguranca

Credenciais e senhas nao devem ser versionadas. Devem ficar em banco local ou
arquivo `.env`, sempre ignorados pelo Git.
