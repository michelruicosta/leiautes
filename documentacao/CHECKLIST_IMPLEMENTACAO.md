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
- [x] Commit: documentacao inicial.

## 2. Base do backend

- [x] Criar estrutura `backend/app`.
- [x] Criar `backend/requirements-api.txt`.
- [x] Criar `app/main.py` com FastAPI.
- [x] Criar rotas `health`.
- [x] Criar `config.py`.
- [x] Criar camada de persistencia inicial.
- [x] Commit: base do backend.

## 3. Persistencia

- [x] Criar banco SQLite.
- [x] Criar tabelas de configuracoes.
- [x] Criar tabelas de usuarios/perfis.
- [x] Criar tabelas de leiautes monitorados.
- [x] Criar tabelas de execucoes.
- [x] Criar tabelas de arquivos e versoes.
- [x] Criar tabelas de alteracoes detectadas.
- [x] Commit: persistencia inicial.

## 4. Migracao do robo

- [ ] Separar coleta de paginas Bacen.
- [ ] Separar extracao de anexos.
- [ ] Separar verificacao de metadados.
- [ ] Separar download para historico.
- [x] Preservar envio de e-mail atual.
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

- [x] Criar estrutura `frontend`.
- [x] Configurar React + Vite + TypeScript.
- [x] Reaproveitar padrao visual do `normativos_ia`.
- [x] Criar `AppShell`.
- [x] Criar tela de login.
- [x] Commit: base do frontend.

## 7. Telas principais

- [x] Dashboard.
- [x] Leiautes.
- [ ] Alteracoes.
- [ ] Detalhe da alteracao.
- [ ] E-mail do gestor.
- [x] Robo.
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
