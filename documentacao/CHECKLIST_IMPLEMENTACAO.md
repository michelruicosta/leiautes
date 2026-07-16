# Checklist de Implementacao

Este checklist sera usado para trabalhar em commits pequenos e rastreaveis.

## 0. Preparacao

- [x] Analisar projeto atual.
- [x] Analisar referencia `normativos_ia`.
- [x] Criar prototipo visual das telas.
- [x] Validar menus finais com a usuaria.
- [x] Criar branch de trabalho.

## 1. Documentacao e arquitetura

- [x] Documentar arquitetura alvo.
- [x] Documentar checklist de implementacao.
- [x] Documentar menus e parametros.
- [ ] Commit: documentacao inicial.

## 2. Base do backend

- [ ] Criar estrutura `backend/app`.
- [ ] Criar `backend/requirements-api.txt`.
- [ ] Criar `app/main.py` com FastAPI.
- [ ] Criar rotas `health`.
- [ ] Criar `config.py`.
- [ ] Criar camada de persistencia inicial.
- [ ] Commit: base do backend.

## 3. Persistencia

- [ ] Criar banco SQLite.
- [ ] Criar tabelas de configuracoes.
- [ ] Criar tabelas de usuarios/perfis.
- [ ] Criar tabelas de leiautes monitorados.
- [ ] Criar tabelas de execucoes.
- [ ] Criar tabelas de arquivos e versoes.
- [ ] Criar tabelas de alteracoes detectadas.
- [ ] Commit: persistencia inicial.

## 4. Migracao do robo

- [ ] Separar coleta de paginas Bacen.
- [ ] Separar extracao de anexos.
- [ ] Separar verificacao de metadados.
- [ ] Separar download para historico.
- [ ] Preservar envio de e-mail atual.
- [ ] Ler parametros do banco/configuracao.
- [ ] Commit: motor do robo modularizado.

## 5. Comparacao de versoes

- [ ] Comparar arquivos PDF por texto extraido.
- [ ] Comparar XSD/XML.
- [ ] Comparar XLS/XLSX.
- [ ] Gerar resumo estruturado das diferencas.
- [ ] Gravar diferencas no banco.
- [ ] Commit: comparacao de arquivos.

## 6. Base do frontend

- [ ] Criar estrutura `frontend`.
- [ ] Configurar React + Vite + TypeScript.
- [ ] Reaproveitar padrao visual do `normativos_ia`.
- [ ] Criar `AppShell`.
- [ ] Criar tela de login.
- [ ] Commit: base do frontend.

## 7. Telas principais

- [ ] Dashboard.
- [ ] Leiautes.
- [ ] Alteracoes.
- [ ] Detalhe da alteracao.
- [ ] E-mail do gestor.
- [ ] Robo.
- [ ] Configuracoes.
- [ ] Usuarios e perfis.
- [ ] Commit: telas principais.

## 8. Integracao frontend/backend

- [ ] Criar cliente API.
- [ ] Integrar dashboard.
- [ ] Integrar configuracoes.
- [ ] Integrar leiautes.
- [ ] Integrar alteracoes.
- [ ] Integrar execucao manual do robo.
- [ ] Commit: integracao inicial.

## 9. Testes e validacao

- [ ] Testar execucao sem alteracao.
- [ ] Testar execucao com arquivo novo.
- [ ] Testar execucao com arquivo alterado.
- [ ] Testar pre-visualizacao de e-mail.
- [ ] Testar envio de e-mail.
- [ ] Testar login e perfis.
- [ ] Commit: ajustes de validacao.

## 10. Deploy

- [ ] Ajustar `run.sh`.
- [ ] Ajustar cron/agenda.
- [ ] Build frontend.
- [ ] Subir backend.
- [ ] Validar em ambiente servidor.
- [ ] Commit: preparacao de deploy.
- [ ] Push final.
