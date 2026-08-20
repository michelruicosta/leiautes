# Pendências — Leiautes Bacen

Última atualização: **2026-08-20**

## Em aberto

### 🟡 Histórico — botão Detalhes na tela vs planilha Exportar

**Contexto:** Na aba Histórico (hoje tela Alterações), a coluna de ação foi renomeada para **Alterações** e o botão **Detalhes** (modal com evidências Entrou/Mudou/Saiu) permanece por enquanto.

**Dúvida futura:** Ver as alterações na tela pode ser redundante quando o usuário já tem a planilha **Exportar** (histórico completo no mesmo espírito do e-mail). Avaliar se o modal Detalhes deve ser removido ou simplificado.

**Decisão atual:** Manter Detalhes. Revisar depois da reforma Histórico / Versões de Arquivos.

**Não fazer agora:** Remover o modal ou a coluna.

### ✅ Histórico e Versões — mapa implementado (20/08)

Entregue no código:
- Menu **Histórico e Versões** + abas Histórico | Versões de Arquivos
- Exportar único (histórico completo); sem card de planilhas; filtros sem Status
- API `/versoes` + download; badge **Fora do site** (vigência anterior à mais recente da família)

### 🟡 Robô enxuto (mapa fechado — detalhar na implementação)

**Robô** fica só com log de execução (sucesso/erro + motivo do erro). Consulta de conteúdo/diffs sai para **Histórico**; download de arquivos para **Versões**. Detalhe fino da UI do Robô ainda não foi desenhado item a item.

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
- Badge na coluna Arquivo quando a URL não está mais no Bacen mas a cópia local existe: rótulo **Fora do site** (incluir nesta versão da tela)
- Cabeçalho: título **Histórico e Versões**; subtítulo *“Consultar o que o robô detectou e baixar arquivos guardados.”*; abas Histórico | Versões de Arquivos; **Exportar** só na aba Histórico; aba padrão = Histórico; remover card “Planilhas disponíveis” e os dois botões antigos de Excel
