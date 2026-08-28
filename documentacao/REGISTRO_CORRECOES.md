# Registro de correções — Leiautes Bacen

## 2026-08-27 23:15 — Publicado no site (Perfil e esqueci senha)

🔎 **Em miúdos:** o site no ar ficou igual ao combinado neste PC: senha no portal; neste app, só entrar e sair.

- **Problema:** as mudanças ainda estavam só neste PC.
- **Causa raiz:** falta publicar na VPS depois do OK.
- **Correção:** commit `f87db25` na `main`, tela gerada de novo no servidor, serviço reiniciado.
- **Validação:** ✅ API no servidor respondeu ok; tela no ar com e-mail, senha, Entrar e Portal de apps — sem “Esqueceu a senha?”.

## 2026-08-27 — Perfil e esqueci senha saem do app

🔎 **Em miúdos:** neste app a pessoa não troca senha nem pede senha nova. Isso fica no portal.

- **Problema:** o menu do nome tinha Perfil e o login tinha “Esqueceu a senha?”.
- **Causa raiz:** a senha passou a ser do portal; o app ainda mostrava o caminho antigo.
- **Correção:** menu do nome só Portal de apps e Sair; login só Entrar e o link do portal.
- **Validação:** ✅ neste PC e no site (`f87db25`).

## 2026-08-27 — Checklist de senha e esqueci senha

🔎 **Em miúdos:** na criação/troca de senha neste app, a lista fica verde na hora. Pedir senha nova passou a chegar na caixa (depois o link saiu da tela).

- **Problema:** a lista de requisitos não aparecia no admin; o esqueci senha não enviava e-mail.
- **Causa raiz:** o admin não usava a mesma lista ao vivo; o envio de senha temporária não estava ligado.
- **Correção:** lista verde ao digitar; e-mail com senha temporária na API.
- **Validação:** ✅ teste neste PC (e-mail chegou). O link “Esqueceu a senha?” saiu da tela no mesmo dia, por decisão do portal.

## 2026-08-27 — Cadastro de Leiautes na Administração

**O que era:** a tela ficava em Operação, junto com o monitoramento.

**O que passou a ser:** fica em Administração, porque cadastrar leiautes é papel do administrador.

**No ar:** commit `712d8b4` (push + site).
