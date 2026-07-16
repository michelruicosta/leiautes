import { useEffect, useState } from "react";
import { obterDashboard } from "../api/leiautes";
import type { DashboardResponse } from "../api/types";

export default function DashboardPage() {
  const [dados, setDados] = useState<DashboardResponse | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    obterDashboard().then(setDados).catch(() => setErro("API indisponível."));
  }, []);

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-sub">Visão executiva do monitoramento de leiautes Bacen.</p>
        </div>
        <button type="button" className="btn-novo">
          Executar robô
        </button>
      </div>

      {erro && <p className="erro">{erro}</p>}

      <div className="cards-resumo">
        <article className="card">
          <h2>Última execução</h2>
          <p className="numero-grande">{dados?.ultima_execucao?.iniciado_em ?? "—"}</p>
          <p className="meta">{dados?.ultima_execucao?.status ?? "Sem registro"}</p>
        </article>
        <article className="card">
          <h2>Leiautes verificados</h2>
          <p className="numero-grande">{dados?.qtd_leiautes ?? 0}</p>
          <p className="meta">cadastros ativos</p>
        </article>
        <article className="card">
          <h2>Arquivos monitorados</h2>
          <p className="numero-grande">{dados?.qtd_arquivos ?? 0}</p>
          <p className="meta">com histórico salvo</p>
        </article>
        <article className="card">
          <h2>Alterações</h2>
          <p className="numero-grande">{dados?.qtd_alteracoes ?? 0}</p>
          <p className="meta">detectadas no histórico</p>
        </article>
      </div>
    </div>
  );
}
