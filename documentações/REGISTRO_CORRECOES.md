# Registro de correções — Leiautes Bacen

Histórico vivo de tudo que foi corrigido. Ler antes de qualquer correção.

---

## 🔴 REGRAS INVIOLÁVEIS — não reverter sem decisão explícita

| # | Regra | Por quê não reverter |
|---|-------|----------------------|
| R1 | Nunca commitar `.env` ou credenciais | Segurança |
| R2 | Sem Perfil neste app | Senha fica no portal; confirmado por Michel em 01/09 |
| R3 | Cadastro de leiautes só em Administração | Não é tela de operação do dia a dia |

---

## Formato de cada entrada

```
### AAAA-MM-DD HH:MM — Título curto

**🔎 Em miúdos:** uma linha em linguagem simples
**Problema:** sintoma visível
**Causa raiz:** origem real do problema
**Correção:** o que foi mudado e em quais arquivos
**Validação:** ✅ VALIDADO ou ⚠️ VALIDAÇÃO PENDENTE com critério mensurável
```

---

<!-- Entradas mais recentes primeiro -->

### 2026-09-01 14:25 — Cadernos de bordo no molde do Normativos

**🔎 Em miúdos:** os cadernos deste projeto passaram a ter o mesmo jeito dos do Normativos: o que está no ar, o que ainda falta e o que é só história.
**Problema:** a lista de pendências misturava o que já tinha acabado com mapa antigo; o caderno da sessão não batia com o molde do outro app.
**Causa raiz:** os cadernos cresceram a cada sessão e itens prontos não saíram da lista do que falta.
**Correção:** pasta `documentações/` com pendências e registro; `SESSAO_ATUAL.md` curto; `documentacao/ESTADO_PROJETO.md` e índice; `INICIO_CHAT.md`; regra de gestor. Pendências antigas já feitas vieram para este registro.
**Validação:** ✅ VALIDADO — Michel fechou a sessão em 01/09 15:15 depois de ver o molde.

### 2026-09-01 12:25 — Chamado arquivado (sem Perfil neste app)

**🔎 Em miúdos:** Michel conferiu depois de uns dias: neste app não pode ter Perfil. Continua certo. Chamado encerrado.
**Problema:** reabrir o chat antigo e não saber se ainda valia.
**Causa raiz:** o bordo tinha parado em 27/08; o combinado já estava no site.
**Correção:** conferência no código — menu só Portal de apps e Sair.
**Validação:** ✅ VALIDADO — Michel, 01/09.

### 2026-08-27 23:15 — Publicado no site (Perfil e esqueci senha)

**🔎 Em miúdos:** o site no ar ficou igual ao combinado neste PC: senha no portal; neste app, só entrar e sair.
**Problema:** as mudanças ainda estavam só neste PC.
**Causa raiz:** falta publicar na VPS depois do OK.
**Correção:** commit `f87db25` na `main`, tela gerada de novo no servidor, serviço reiniciado.
**Validação:** ✅ VALIDADO — API no servidor ok; tela no ar com e-mail, senha, Entrar e Portal de apps — sem “Esqueceu a senha?”.

### 2026-08-27 — Perfil e esqueci senha saem do app

**🔎 Em miúdos:** neste app a pessoa não troca senha nem pede senha nova. Isso fica no portal.
**Problema:** o menu do nome tinha Perfil e o login tinha “Esqueceu a senha?”.
**Causa raiz:** a senha passou a ser do portal; o app ainda mostrava o caminho antigo.
**Correção:** menu do nome só Portal de apps e Sair; login só Entrar e o link do portal.
**Validação:** ✅ VALIDADO — neste PC e no site (`f87db25`).

### 2026-08-27 — Checklist de senha ao vivo

**🔎 Em miúdos:** na criação/troca de senha neste app, a lista fica verde na hora.
**Problema:** a lista de requisitos não aparecia no admin.
**Causa raiz:** o admin não usava a mesma lista ao vivo.
**Correção:** lista verde ao digitar (8 caracteres, maiúscula, minúscula, número, especial).
**Validação:** ✅ VALIDADO — teste neste PC.

### 2026-08-27 — Cadastro de Leiautes na Administração

**🔎 Em miúdos:** cadastrar leiautes saiu da operação do dia a dia e foi para Administração.
**Problema:** a tela ficava em Operação, junto com o monitoramento.
**Causa raiz:** cadastrar leiautes é papel do administrador, não do operador.
**Correção:** menu — primeiro item de Administração; operador e gestor não veem o cadastro.
**Validação:** ✅ VALIDADO — produção, commit `712d8b4`.

### 2026-08-26 — Comparação de arquivos + e-mail do gestor

**🔎 Em miúdos:** o recado ao gestor mostra o que mudou, arquivo a arquivo, com o modelo combinado.
**Problema:** papéis com nome diferente e empate de mês no nome precisavam de regra clara.
**Causa raiz:** o comparador não tinha os empates cravados (v / vi) nem o quadro do e-mail no formato final.
**Correção:** críticas DLO/DRM, instruções DRM/DDR/SCD e leiaute DDR cravados; e-mail com quadro por arquivo; planilha sem coluna “O que fazer”.
**Validação:** ✅ VALIDADO — ensaio de tipos/cenários por Michel. Ver `documentacao/COMPARACAO_ARQUIVOS.md`.

### 2026-08-24 — Robô novo em produção; legado desligado

**🔎 Em miúdos:** o robô novo passou a ser o que roda no servidor; o antigo foi desligado.
**Problema:** dois caminhos no servidor podiam se cruzar.
**Causa raiz:** agenda antiga ainda existia nos usuários do servidor.
**Correção:** cron legado comentado; agenda na tela **Robô**; e-mail só quando há mudança.
**Validação:** ✅ VALIDADO — legado e novo bateram em 0 mudanças no mesmo dia; teste de e-mail ok.

### 2026-08-24 — Monitoramento MCC + DRSAC 2030

**🔎 Em miúdos:** o robô passou a visitar também as páginas MCC e DRSAC 2030 no site do Bacen.
**Problema:** esses leiautes ficavam de fora.
**Causa raiz:** a página MCC não lista os arquivos do jeito das outras; DRSAC não estava no cadastro.
**Correção:** três arquivos fixos do MCC + PDF e planilha da página; DRSAC com PDF, planilha, zip e o arquivo de leiaute.
**Validação:** ✅ VALIDADO — tela Leiautes com 8 itens e primeira baseline em Alterações. Commit `350df20`.

### 2026-08-24 — Planilha unificada do gestor

**🔎 Em miúdos:** uma planilha só, para o e-mail e para o botão Exportar.
**Problema:** formatos diferentes entre o recado e o arquivo baixado.
**Causa raiz:** duas montagens da mesma informação.
**Correção:** abas Resumo, O que mudou, Só aviso; link Abrir no site do Bacen.
**Validação:** ✅ VALIDADO — modelo em uso.

### 2026-08-21 — Modelo do e-mail em Configurações

**🔎 Em miúdos:** o modelo do comunicado ficou só em Configurações; a tela paralela de prévia saiu.
**Problema:** dois lugares para o mesmo modelo.
**Causa raiz:** tela “E-mail do gestor” duplicava Configurações.
**Correção:** assunto, envio e anexos em **Configurações → Modelo do e-mail**; destinatários na flag de usuários; corpo montado pelo robô.
**Validação:** ✅ VALIDADO — decisão Michel.

### 2026-08-21 — Dashboard sem Executar robô

**🔎 Em miúdos:** o botão de rodar o robô saiu do painel inicial; execução só na tela Robô.
**Problema:** dois jeitos de disparar o mesmo robô.
**Causa raiz:** atalho no Dashboard além da tela própria.
**Correção:** botão removido do Dashboard.
**Validação:** ✅ VALIDADO — decisão Michel.

### 2026-08-21 — Histórico: Detalhes e Exportar

**🔎 Em miúdos:** na lista do histórico ficam o botão Detalhes (olhada rápida) e o Exportar (planilha completa).
**Problema:** dúvida se o Detalhes deveria sair depois do Exportar.
**Causa raiz:** dois jeitos de ver a mesma mudança, com papéis diferentes.
**Correção:** os dois ficam. Revisar só se a operação pedir no uso real.
**Validação:** ✅ VALIDADO — decisão Michel.

### 2026-08-20 — Histórico e Versões + robô enxuto

**🔎 Em miúdos:** uma tela para consultar o que o robô detectou e baixar arquivos guardados; a tela Robô ficou só para operar.
**Problema:** consulta de conteúdo misturada com operação do robô.
**Causa raiz:** o mapa das telas ainda não estava fechado.
**Correção:** menu Histórico e Versões (abas Histórico e Versões de Arquivos); Robô só executar + log; e-mail só com mudanças; agenda na tela.
**Validação:** ✅ VALIDADO — no código e em produção.
