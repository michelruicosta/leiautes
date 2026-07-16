# Telas e Parametros

## Menus

Os menus devem seguir o padrao visual e operacional do `normativos_ia`.

### Login

Campos:

- e-mail;
- senha;
- recuperar senha.

Conteudos:

- logo;
- nome da empresa;
- subtitulo do sistema.

### Dashboard

Conteudos:

- ultima execucao;
- status do robo;
- quantidade de leiautes verificados;
- quantidade de arquivos alterados;
- e-mails enviados;
- ultimas alteracoes;
- avisos operacionais.

### Leiautes

Conteudos:

- codigo/sigla do leiaute;
- nome;
- URL Bacen;
- categoria;
- tipos de arquivo monitorados;
- status ativo/inativo;
- ultima leitura.

Leiautes iniciais:

- DDR 2011;
- DRM 2060;
- DLO 2061;
- DLI 2062;
- DRL 2160;
- SCD 4111.

### Alteracoes

Conteudos:

- execucao;
- leiaute;
- arquivo;
- tipo;
- versao anterior;
- versao atual;
- resumo executivo;
- itens incluidos;
- itens removidos;
- itens alterados;
- impacto sugerido;
- status de revisao/envio.

### E-mail do gestor

Conteudos:

- assunto;
- destinatarios;
- resumo executivo;
- diferencas por leiaute;
- anexos;
- observacao manual;
- pre-visualizacao;
- botao de envio.

### Robo

Conteudos:

- status ligado/desligado;
- executar agora;
- agenda;
- feriados;
- historico de execucoes;
- log resumido;
- etapa atual.

### Configuracoes

Abas sugeridas:

- Empresa;
- E-mail;
- Monitoramento;
- URLs Bacen;
- Anexos;
- Comparacao;
- Status publico.

Parametros migrados do script:

- `CONNECT_TIMEOUT`;
- `READ_TIMEOUT`;
- `QUIET_BASELINE`;
- `ONLY_ATUAL`;
- `EXCLUDE_PATTERNS`;
- `ATTACH_CHANGED_FILES`;
- `MAX_ATTACHMENTS`;
- `MAX_SINGLE_ATTACH_SIZE`;
- `MAX_TOTAL_ATTACH_SIZE`;
- `SEND_EMAIL_WHEN_NO_CHANGES`;
- lista `urls`;
- `TAIL_PATH_BASE`;
- `LOG_PATH_BASE`;
- `CONFIG_PATH`;
- `LOGO_PATH`;
- assunto padrao do e-mail;
- destinatarios;
- SMTP;
- usuario e senha de envio.

### Usuarios e perfis

Perfis iniciais:

- Operador;
- Gestor;
- Administrador.

Permissoes previstas:

- Dashboard;
- Leiautes;
- Alteracoes;
- E-mail do gestor;
- Robo;
- Configuracoes;
- Usuarios e perfis.

## Observacoes de implementacao

- Seguir nomes e padroes de componentes do `normativos_ia` sempre que possivel.
- Evitar criar novo design system.
- Evitar configurar no codigo qualquer dado que precise mudar em operacao.
- Manter compatibilidade com execucao por `run.sh` durante a migracao.
