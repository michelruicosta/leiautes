# Comparação de arquivos — regra e mapa dos cadastros

Última atualização: **2026-08-26**  
Inventário: produção (`leiautes.db`), arquivos ainda no site do Banco Central.  
**8 cadastros · 118 arquivos.**

Este texto é a referência para o robô e para consultas futuras. Não comparar “porque a extensão é a mesma”.

---

## O que o robô pode e não pode fazer

1. **Mesmo papel** (miolo do nome igual; só muda versão ou competência) → **compara sempre**.  
   Ex.: `2061_v10.xsd` com `2061_v11.xsd`; Modelo (contas) de um mês com o do mês seguinte.

2. **Nome diferente, mesmo papel cravado** → compara (DLO críticas V5, DRM instruções/críticas, DDR instruções e leiaute XLS, SCD instruções, XSD do DLI). Aviso: **o nome no site mudou**.

3. **Nome diferente, XSD ainda sem mapa** → compara **somente** se naquele cadastro só existia um arquivo de validação.

4. **Dois papéis no mesmo tipo** → **não compara**.  
   Ex.: Modelo vs Contas; `AMCC001` vs `AMCC002`.

Se a dúvida permanecer, o robô **não inventa o par**.

Código: `escolher_nome_versao_parente` em `persistencia/arquivos_db.py`.  
Testes: `persistencia/test_versao_parente.py`.

---

## O que o robô lista (e o que ignora) no arquivo de validação

Não é comparação linha a linha (como o Notepad++). Se fosse, quase tudo “mudaria” só porque um bloco novo empurrou as linhas para baixo.

**Lista (conta para o alerta):**

- Campo ou tipo novo, removido ou com outra obrigatoriedade
- A **receita** do tipo: o que aceita (só número vs letra e número, tamanho, lista de códigos)
- Chave de unicidade (não repetir o mesmo código)
- Data-base e “atualizado em” no cabeçalho

**Não lista (de propósito):**

- Espaço, indentação, linha em branco
- Linha que só andou para baixo porque entrou texto acima
- Comentário que não fala de data/versão

No DLI v3→v5 isso explica as 13 peças do COSIF **e** o CNPJ (8 números → 8 letras/números) e a data-base 03/2019 → 02/2026, que a versão antiga do robô não listava.

Código: `_comparar_xsd` em `backend/app/services/comparador_arquivos.py`.  
Testes: `backend/app/services/test_comparador_xsd.py`.

---

## Casos já combinados (Michel, 26/08/2026)

| Situação | Decisão |
|---|---|
| DLI — `2062_v2` / `2062_v3` e `Esquema de validação XSD v5.xsd` | **Compara**. Aviso: nome no site mudou. |
| DLO — Modelo vs Leiaute vs Configuração vs Críticas | **Não cruza** só porque são planilha. |
| DLO — críticas `2061-…` e `…V5 Ajustada` | **Compara** (mesmo papel). |
| DRM — instruções v2…v11 (mês no nome) e críticas `…2060` / `…V5_Jul26` | **Compara**. |
| DDR — dois PDFs de instruções; dois XLS de leiaute publicação | **Compara**. |
| SCD — dois PDFs de instruções | **Compara**. |
| MCC — `AMCC001`, `AMCC002`, `AMCCComum` | **Não cruza**. |

---

## Qual versão anterior usar (quando há várias)

O robô **não** usa a data em que gravamos o cadastro (primeiro dia em que vimos o arquivo). Na primeira leitura, muitos arquivos entram no mesmo dia — essa data não diz qual é o mais novo no Banco Central.

Ele usa, neste papel, nesta ordem:

1. **Mês no nome do arquivo** (ex.: `202607`) — pega o mês anterior mais próximo.
2. Se o mês for **igual**: o número **v** mais alto (`v2` ganha de `v1`).
3. Se o **v** também for igual: o **vi** mais alto (`v8-vi9` ganha de `v8-vi8`).

### Sim, existe mês igual no site hoje

| Cadastro | Papel | Mesmo mês | Arquivos |
|---|---|---|---|
| DLO-2061 | Modelo (contas) | 202607 | `…-v1-vi1-…` e `…-v2-vi2-…` |
| DLO-2061 | Instruções | 202607 | `…-v7-vi8-…` e `…-v8-vi9-…` |
| DLI-2062 | Planilha de configuração | 202607 | `…-v1- Planilha…` e `…-v2 Planilha Configuração…` |

Nesses casos o robô compara com o de **versão mais alta** daquele mês, não com os dois.

---

## Mapa por cadastro

Arquivos agrupados pelo **papel** (função no site). “Compara versões” = o robô liga as edições daquele papel. “Não cruzar” = não misturar com outro papel do mesmo tipo.

### DDR-2011 (11 arquivos)

| Tipo | Papel | Arquivos | Regra |
|---|---|---|---|
| PDF | Instruções | `2011-202407-v7-vi7-Instruções de Preenchimento.pdf`, `Instruções de Preenchimento  2011 - versão publicação V3.01032021.pdf` | Compara (nome mudou) |
| XLS | Configuração Dez/2020 | `Configuração DDR_2011 (Válida a partir de Dezembro 2020).xls` | Não cruzar |
| XLS | Configuração Sistema Limites | `DDR 2011 Configuração Sistema Limites 01072023.xlsx.xls` | Não cruzar |
| XLS | Leiaute publicação | `Leiaute DDR - 2011 Versão Publicação.xls`, `Leiaute_DDR_2011_Versao_Publicacao.v5 01072023.xls` | Compara (nome mudou) |
| XLSX | Configuração 2023 | `Configuração do Documento 2011 - Versão de 01072023.xlsx` | Não cruzar |
| XLSX | Críticas | `Criticas De Pós-processamento_2011_V2.xlsx` | Não cruzar |
| XLSX | Tabela de conversão | `DDR - Estrutura de campos - Tabela de conversão - Versão Publicação.V7 - 01072023.xlsx` | Não cruzar |
| XLSX | Tabela de correlação | `Tabela de Correlação de Campos 01.12.2020.xlsx` | Não cruzar |
| XSD | Validação (único neste cadastro) | `DDR_2011_XSD_V01072020.xsd` | Se o nome mudar, compara e avisa |

### DRM-2060 (17 arquivos)

| Tipo | Papel | Arquivos | Regra |
|---|---|---|---|
| PDF | Instruções | `InstrucoesPreenchimentoDRM_v2.pdf` … `v11_Jan25.pdf` | Compara versões (mês no nome) |
| PDF | Críticas | `Criticas_Pos_Processamento_2060.pdf`, `…_V5_Jul26.pdf` | Compara (nome mudou) |
| PDF | Lista de erros | `Lista_de_Erros_DRM.pdf` | Não cruzar |
| XLS | Leiaute 2040 (legado no site) | `DRM2040_leiaute_v2.xls` | Não misturar com 2060 |
| XLS | Leiaute 2060 | `DRM2060_leiaute_v2.xls` | Não cruzar |
| XLSX | Leiaute DRM | `DRM_leiaute_v3.xlsx`, `DRM_leiaute_v4.xlsx` | Compara versões |

### DLO-2061 (21 arquivos)

| Tipo | Papel | Arquivos | Regra |
|---|---|---|---|
| PDF | Instruções | `2061-202508-v2-vi4-Instruções…` até `2061-202607-v8-vi9-…` (4 arquivos) | Compara versões |
| PDF | Participação não controladores | `Participacao_Nao_Controladores_Patrimonio_Referencia.pdf` | Não cruzar |
| XLSX | Modelo documento (contas) | 4 arquivos `2061-…-Modelo documento (contas).xlsx` | Compara versões; **nunca** com Leiaute / Configuração / Críticas |
| XLSX | Leiaute do DLO | 3 arquivos `2061-…-Leiaute do DLO.xlsx` | Compara versões |
| XLSX | Planilha de configuração | 3 arquivos `2061-…-Planilha de configuração.xlsx` | Compara versões |
| XLSX | Críticas | `2061-202407-v1-…`, `2061-202411-v3-…`, `Críticas de Pós-Processamento DLO_2061_V5 Ajustada.xlsx` | Compara (nome mudou) |
| XSD | Validação (único) | `2061_v9.xsd`, `2061_v10.xsd`, `2061_v11.xsd` | Compara versões; se o nome mudar, compara e avisa |

### DLI-2062 (24 arquivos)

| Tipo | Papel | Arquivos | Regra |
|---|---|---|---|
| PDF | Instruções | 3 arquivos `2062-…-Instruções de Preenchimento.pdf` | Compara versões |
| PDF | Alterações abril 2023 | `Alterações Instruções… Abril 2023_republicação v3.pdf` | Não cruzar |
| PDF | Alterações outubro 2023 | `Alterações Instruções… Outubro 2023 v2.pdf` | Não cruzar |
| XLSX | Planilha de configuração | 5× `Planilha de configuração` + `2062-202607-v2 Planilha Configuração.xlsx` | Compara versões |
| XLSX | Leiaute do DLI | 4 arquivos `2062-…-Leiaute do DLI.xlsx` | Compara versões |
| XLSX | Modelo documento (contas) | `2062 - 202411-v1-…`, `2062-202505-v1-…`, `2062-202607-v1-vi1-…` | Compara versões; **nunca** com Leiaute / Configuração |
| XLSX | Partes relacionadas | `Modelo de Cálculo de Partes Relacionadas.xlsx` | Não cruzar |
| XLSX | Modelo publicação abril 2023 | `Modelo DLI publicação_v5 Abril 2023.xlsx` | Não cruzar |
| XLSX | Modelo publicação outubro 2023 | `Modelo DLI publicação_v1 Outubro 2023.xlsx` | Não cruzar |
| XSD | Validação | `2062_v2.xsd`, `2062_v3.xsd`, `Esquema de validação XSD v5.xsd` | **Compara**; aviso: nome no site mudou |

### DRL-2160 (31 arquivos)

Modelo I e modelo II, anexos, subsidiária, relação de contas e modelo de cálculo **não se misturam**. Só compara se o miolo do nome for o mesmo (ex.: `DRL_2160_leiaute_v201801` com `…_v202607`; `Esquema_DRL2160_v1.xsd` com `…_v202607.xsd`).

### SCD-4111 (4 arquivos)

| Tipo | Papel | Arquivos | Regra |
|---|---|---|---|
| PDF | Instruções | PDF longo e `saldosDiariosInstrucoesPreenchimentoV2.pdf` | Compara (nome mudou) |
| XSD | Validação (único) | `XSD_4111.xsd`, `XSD_4111V1.xsd` | Compara versões; se o nome mudar, compara e avisa |

### DRSAC-2030 (5 arquivos)

| Tipo | Papel | Arquivo | Regra |
|---|---|---|---|
| PDF | Instruções | `Instrucoes-de-Preenchimento-DRSAC.pdf` | Não cruzar com perguntas |
| PDF | Perguntas e respostas | `Perguntas-Respostas-DRSAC.pdf` | Não cruzar |
| XLSX | Leiaute | `Leiaute-DRSAC.xlsx` | Só compara se o miolo do nome for o mesmo |
| XSD | Validação | `Leiaute-DRSAC.xsd` | Único XSD; se o nome mudar, compara e avisa |
| ZIP | Pacote dez/2026 | `Leiaute-DRSAC-valido-a-partir-de-dez-2026.zip` | Só compara se o miolo do nome for o mesmo |

### MCC (5 arquivos)

| Tipo | Papel | Arquivo | Regra |
|---|---|---|---|
| PDF | Roteiro / instruções | `MCC-roteiro-externo-instrucoes-de-recursos-e-utilizacao.pdf` | Único PDF |
| XLSX | Layout XML | `MCC-Layout-XML-divulgacao.xlsx` | Único XLSX |
| XSD | AMCC001 | `AMCC001.xsd` | **Não cruzar** com os outros XSD |
| XSD | AMCC002 | `AMCC002.xsd` | **Não cruzar** |
| XSD | AMCCComum | `AMCCComum.xsd` | **Não cruzar** |

---

## Texto para o usuário (quando o nome mudou)

Não usar jargão. Deixar explícito:

> Arquivo novo na página. O nome no site mudou. Comparamos com **{arquivo anterior}**, o último deste mesmo tipo neste cadastro, só para você ver o que mudou.

O marcador técnico no resumo continua com `antes: {nome}` (necessário para o e-mail e a planilha).
