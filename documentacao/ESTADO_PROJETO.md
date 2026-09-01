# Estado do projeto — Leiautes Bacen

Última atualização: **2026-09-01** (cadernos de bordo alinhados ao molde do Normativos)

---

## Marco atual

| Item | Valor |
|------|-------|
| **Fase** | Site no ar e em uso. Robô visita as páginas do Bacen e avisa quando o arquivo muda. |
| **Branch de trabalho** | `main` (não criar ramo novo) |
| **Site** | `https://leiautes-bacen.finaudapps.com.br` |
| **Neste PC** | Tela **5177** · API **8003** |

---

## O que está feito

- Site da equipe (painel, leiautes, o que mudou, robô, histórico, usuários)
- Login pelo portal (sem Perfil nem “Esqueceu a senha?” neste app)
- Cadastro de leiautes só na **Administração**
- Robô novo no servidor; agenda na tela **Robô**; legado desligado
- Páginas MCC e DRSAC 2030 no monitoramento
- Comparação de arquivos e e-mail do gestor (só quando há mudança)
- Checklist verde ao vivo na senha (quando a senha é definida neste app)

---

## Próximo passo imediato

Nenhuma urgente. Abrir o que a operação pedir.

Detalhe vivo: `../SESSAO_ATUAL.md` · o que falta: `../documentações/PENDENCIAS.md`.

---

## Regras em vigor

| Regra | Motivo |
|-------|--------|
| Nunca commitar `.env` ou credenciais | Segurança |
| Não push sem OK explícito | Evitar publicar meio caminho |
| Trabalho só na `main` | Um caderno só, igual ao combinado |
| Sem Perfil neste app | Senha fica no portal |
| Cadastro de leiautes só em Administração | Não é tela de operação do dia a dia |
| E-mail só quando há mudança | Evitar recado vazio |
| Estado só no bordo deste repo | Sem mapa geral neste projeto |
| Correções registradas em `REGISTRO_CORRECOES.md` | Histórico e não-regressão |

---

## Referência cruzada

- Caderno da sessão: [SESSAO_ATUAL.md](../SESSAO_ATUAL.md)
- Pendências: [PENDENCIAS.md](../documentações/PENDENCIAS.md)
- Checklist antigo de fases: [CHECKLIST_IMPLEMENTACAO.md](CHECKLIST_IMPLEMENTACAO.md)
- Arquitetura: [ARQUITETURA_APP_LEIAUTES.md](ARQUITETURA_APP_LEIAUTES.md)
