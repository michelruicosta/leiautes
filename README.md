
# Monitoramento de Leiautes Bacen (Finaud)

Automação desenvolvida para monitorar atualizações nos leiautes do Banco Central (Bacen).  
Verifica novos documentos ou alterações, envia e-mail com log detalhado e atualiza o status da execução em painel público.

## 📁 Estrutura da pasta

```
leiautes/
├── config/                       # Configurações do projeto (ex: config_email.json)
├── logotipo/                     # Logo da Finaud usado nos e-mails HTML
├── logs/                         # Logs de execução do sistema:
│   ├── execucao_YYYYMMDD.log         # Log detalhado da execução principal
│   ├── cron_YYYYMMDD.log             # Log da execução automática via cron
│   ├── monitor_leiautes_YYYYMMDD.log # Log complementar (pode incluir testes ou execuções parciais)
│   ├── execucao_cron.log             # Log curto usado no painel público (_status_tail.txt)
│   ├── execucao_cron.log-YYYYMMDD    # Versões diárias do log de status
│   └── *.gz                          # Logs compactados antigos (backup/rotação)
├── pdfs/                         # (Opcional) PDFs baixados para envio
├── .pki/                         # Cache gerado pelo navegador do Playwright (seguro limpar)
├── runtime/                      # Arquivos temporários da execução (HTMLs, PDFs, etc.)
├── scripts/                      # Scripts Python (principal: verifica_leiautes_finaud.py)
├── venv/                         # Ambiente virtual com dependências Python
├── requirements.txt              # Lista de pacotes (usado no pip install -r)
└── run.sh                        # Script principal que executa o monitoramento
```

---

## 📄 Sobre os logs de execução

Todos os logs são salvos na pasta `/logs`, organizados por data.

### Tipos de logs gerados

- `execucao_YYYYMMDD.log`:  
  Log completo da execução do dia. Mostra passo a passo o que foi feito, anexos encontrados, alterações, e-mail enviado, erros, etc.

- `cron_YYYYMMDD.log`:  
  Log de saída padrão quando o `run.sh` é executado via `crontab`. Serve para depuração rápida.

- `monitor_leiautes_YYYYMMDD.log`:  
  Usado em execuções alternativas, testes manuais ou rodando scripts individuais. Pode complementar o log principal.

- `execucao_cron.log` e `execucao_cron.log-YYYYMMDD`:  
  Arquivos utilizados para gerar o painel de status visível publicamente (`_status_tail.txt`), com mensagens como "🟢 OK", "🟡 AVISO" ou "🔴 ERRO".

- Arquivos `.gz`:  
  Logs compactados automaticamente pelo sistema para liberar espaço.

---

### 📌 Dica

Para verificar rapidamente se a execução diária funcionou corretamente:

```bash
tail -n 30 logs/execucao_$(date +%Y%m%d).log
```

---

## ▶️ Como executar o projeto

### 🧪 Execução manual

Ative o ambiente virtual:

```bash
source venv/bin/activate
```

Execute o script principal:

```bash
./run.sh
```

Ou diretamente com Python:

```bash
python3 scripts/verifica_leiautes_finaud.py
```

### ⏰ Execução automática via cron

Para agendar a execução diária automática, adicione esta linha ao crontab do usuário (crontab -e):

```bash
0 9 * * * /home/tsalachtech.com.br/apps/leiautes/run.sh >> /home/tsalachtech.com.br/apps/leiautes/logs/cron_$(date +\%Y\%m\%d).log 2>&1
```

Essa linha roda o script todos os dias às 9h da manhã, registrando a saída e erros no log do dia.

---

## ✅ Verificando a execução

- Log completo do dia:  
  `/home/tsalachtech.com.br/apps/leiautes/logs/execucao_YYYYMMDD.log`

- Confirme se o e-mail foi enviado com o log e anexos.

---

## 📬 Configuração de e-mail

As credenciais e dados de envio ficam no arquivo:

```
config/config_email.json
```

Exemplo de estrutura:

```json
{
  "from": "seu-email@dominio.com",
  "to": ["destinatario1@empresa.com", "destinatario2@empresa.com"],
  "senha": "senha-ou-token-de-aplicativo",
  "assunto_email": "Monitoramento Leiautes Bacen",
  "enviar_sempre": true
}
```

### Campos principais:

- `from`: endereço de e-mail do remetente (usado na autenticação)  
- `to`: lista de destinatários que receberão o e-mail  
- `senha`: senha do app (ou token gerado no Gmail, Outlook etc.)  
- `assunto_email`: aparece no título do e-mail enviado  
- `enviar_sempre`: se `true`, o e-mail será enviado mesmo que nenhum documento novo seja encontrado  

⚠️ **Nunca versionar esse arquivo com senha no GitHub ou repositórios públicos!**

---

> docs(README): melhora documentação com estrutura, logs e execução
