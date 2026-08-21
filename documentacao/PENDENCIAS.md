# Pendências — Leiautes Bacen

Última atualização: **2026-08-21**

## Em aberto

*(nenhuma urgente)*

## Fechadas recentemente

### ✅ Histórico — botão Detalhes mantido (21/08)

**Decisão Michel:** manter o botão **Detalhes** (modal Entrou/Mudou/Saiu) **e** o **Exportar** Excel.

- Detalhes = olhada rápida de **uma** linha, na tela  
- Exportar = histórico completo para filtrar / guardar / encaminhar  

Não remover nem simplificar agora. Revisar só se a operação pedir no uso real.

### ✅ E-mail só com mudanças + agenda na tela (20/08)

- Motor lê `email.enviar_sem_alteracao` e `email.anexar_alterados` da Configurações
- Produção: `email.enviar_sem_alteracao=false` (e-mail só com alterações)
- Agenda em **Robô → Agenda**; cron `* * * * * --checar-agenda`; garantia 17:30 permanece fixa

### ✅ Robô enxuto (20/08)

Tela **Robô** reduzida a: executar + log (status sucesso/erro + motivo). Contagens de leiautes/arquivos/alterações/e-mails saíram da tabela — consulta de conteúdo em **Histórico e Versões**. Botão **Executar agora** continua sem e-mail (API de teste).

### ✅ Histórico e Versões — mapa implementado (20/08)

Entregue no código:
- Menu **Histórico e Versões** + abas Histórico | Versões de Arquivos
- Exportar único (histórico completo); sem card de planilhas; filtros sem Status
- API `/versoes` + download; badge **Fora do site** via HEAD na URL Bacen (cache 12h)

---

## Mapa fechado — Histórico e Versões (20/08)

### Papéis das telas

| Tela | Função |
|------|--------|
| **Histórico e Versões** (menu) | Abas: Histórico + Versões de Arquivos |
| **Histórico** | O que o robô detectou / consultar mudanças + Exportar Excel completo |
| **Versões de Arquivos** | Listar/baixar cópias em storage; **sem** diff; badge **Fora do site** |
| **Robô** | Operar + log sucesso/erro (sem ser a tela de consulta de conteúdo) |

### Histórico

- Filtros: Buscar · Leiaute · Tipo (**sem** Status)
- Colunas: Data · Leiaute · Arquivo · Tipo · Resumo · **Alterações** (botão Detalhes)
- Canto direito: **Exportar** — 1 XLSX com histórico completo de mudanças (estilo e-mail, filtrável no Excel)
- Remover: dois botões antigos de planilha + card “Planilhas disponíveis”
- Aba padrão ao abrir a página

### Versões de Arquivos

- Filtros: Buscar · Leiaute · Tipo
- Colunas: Capturado em · Leiaute · Arquivo (+ badge **Fora do site**) · Vigência · Tipo · **Download**
- Sem Exportar, sem tamanho, sem diff

### Cabeçalho

- Título: **Histórico e Versões**
- Subtítulo: *“Consultar o que o robô detectou e baixar arquivos guardados.”*
- Exportar só na aba Histórico

---

## Ordem sugerida de implementação

1. **Renomear menu/tela** + abas (Histórico | Versões) com Histórico = conteúdo atual adaptado
2. **Exportar** único + remover card/botões antigos; filtros sem Status; coluna Alterações
3. **API + aba Versões** (listar, vigência, Download)
4. **Badge Fora do site** (marcar URL ausente no Bacen)
5. **Robô enxuto** (depois do mapa fino ou em paralelo leve)

---

## Decisões de produto (rascunho — conversa 20/08)

- Menu/tela: **Histórico e Versões**, com abas **Histórico** e **Versões de Arquivos**
- **Robô:** só log de execução (sucesso/erro + motivo do erro)
- **Histórico:** o que já rodou + diffs; **Exportar** = 1 Excel com histórico completo de mudanças
- **Versões de Arquivos:** só listar/baixar cópias guardadas (**sem** diff)
- Filtros Histórico: Buscar · Leiaute · Tipo (**sem** Status)
- Coluna da lista Histórico: **Alterações** (antes “Ação”)
- Colunas Versões: Capturado em · Leiaute · Arquivo · Vigência · Tipo · botão **Download** (sem tamanho)
- Badge **Fora do site**: validação por **HEAD na URL Bacen** (404 = fora), com cache 12h — **não** por vigência YYYYMM (corrigido 20/08: v1 202607 era 404 e 202508/202509 ainda 200)
- Cabeçalho: título **Histórico e Versões**; subtítulo *“Consultar o que o robô detectou e baixar arquivos guardados.”*; abas Histórico | Versões de Arquivos; **Exportar** só na aba Histórico; aba padrão = Histórico; remover card “Planilhas disponíveis” e os dois botões antigos de Excel
