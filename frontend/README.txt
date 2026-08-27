Frontend — Leiautes Bacen
=========================

Molde: Projeto_Auditoria_IA/frontend/

Dev (API na porta 8003):
  cd frontend
  npm install
  npm run dev

Abre http://localhost:5177 — chamadas /api/* vão para http://127.0.0.1:8003
Não mandar esses endereços se API/UI não estiverem no ar.
Não usar 8001 (Auditoria) nem 5173.

Build produção:
  npm run build
  (saída em frontend/dist/)
