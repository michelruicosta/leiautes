# Pendências — Leiautes Bacen

Última atualização: **2026-08-26**

## Em aberto

*(nenhuma urgente)*

## Fechadas recentemente

### ✅ Comparação de arquivos + e-mail do gestor (26/08)

- Referência: `documentacao/COMPARACAO_ARQUIVOS.md`
- Papéis com nome diferente **cravados** (críticas DLO/DRM, instruções DRM/DDR/SCD, leiaute DDR).
- Mesmo mês no nome: desempate por **v** e depois **vi**.
- Modelo vs Contas e MCC AMCC001/002/Comum continuam **sem** cruzar.
- Comparador XSD lista receita do tipo (CNPJ) e data-base do cabeçalho.
- E-mail: quadro por arquivo, cabeçalho azul, planilha sem coluna “O que fazer”, comparação com o arquivo anterior. Ensaio de tipos/cenários validado por Michel.

### ✅ Robô novo em produção — legado desligado (24/08)

- Cron legado comentado em `tsala9334` e `paine6949` (backup em `/root/backup-cron-leiautes/`)
- Produção: agenda na tela **Robô** + cron root `--checar-agenda`
- Destinatários de alerta: michel@, marcio@, suporte@ (+ michelruicosta@gmail.com no cadastro)
- E-mail só quando há mudança (`enviar_sem_alteracao` desligado)
- Validado: legado e novo bateram em 0 mudanças no mesmo dia; teste de e-mail #50 ok

### ✅ Monitoramento MCC + DRSAC 2030 (24/08)

- Robô passa a visitar as páginas **MCC** e **DRSAC 2030** no site do Bacen
- MCC: 3 XSDs fixos (página Angular não lista links) + PDF e planilha da página
- DRSAC: PDFs, xlsx, zip e `Leiaute-DRSAC.xsd`
- Seed no banco + vínculo correto do leiaute **MCC** (código sem sufixo numérico)
- Validado em produção: tela **Leiautes** (8 leiautes) e primeira baseline em **Alterações**
- Commit `350df20` em `codex/app-leiautes-bacen`

### ✅ Planilha unificada do gestor (24/08)

- Uma planilha para e-mail e **Exportar**: abas **Resumo**, **O que mudou**, **Só aviso**
- Formatação: título por aba, wrap, altura automática, Sim/Não colorido, link **Abrir no site do Bacen**

### ✅ Modelo do e-mail em Configurações (21/08)

**Decisão Michel:** a tela **E-mail do gestor** (prévia paralela) **saiu**.

- Modelo do comunicado: **Configurações → Modelo do e-mail** (assunto, SMTP, anexos, quando enviar)
- Destinatários: **Usuários e perfis** → flag receber alertas
- Corpo em 3 passos: montado pelo **robô** com as mudanças detectadas
- Não manter dois templates (tela vs envio real)

### ✅ Dashboard sem Executar robô (21/08)

Botão **Executar robô** removido do Dashboard — execução só na tela **Robô**.

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
