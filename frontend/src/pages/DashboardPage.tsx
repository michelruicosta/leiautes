import { useEffect, useState } from "react";
import { obterDashboard } from "../api/leiautes";
import type { DashboardResponse } from "../api/types";

function formatarData(valor?: string | null): string {
  if (!valor) return "—";
  const data = new Date(valor);
  if (Number.isNaN(data.getTime())) return valor;
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(data);
}

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

      <div className="dashboard-hero">
        <div>
          <span className="meta">Última execução</span>
          <h2>{formatarData(dados?.ultima_execucao?.iniciado_em)}</h2>
          <p className="meta">{dados?.ultima_execucao?.status ?? "Sem registro"}</p>
        </div>
        <div className="dashboard-hero-numero">
          <span>{dados?.qtd_alteracoes ?? 0}</span>
          <p>alterações detectadas</p>
        </div>
      </div>

      <div className="cards-resumo cards-resumo-dashboard">
        <article className="card resumo-card">
          <span className="resumo-icone">LE</span>
          <h2>Leiautes verificados</h2>
          <p className="numero-grande">{dados?.qtd_leiautes ?? 0}</p>
          <p className="meta">cadastros ativos</p>
        </article>
        <article className="card resumo-card">
          <span className="resumo-icone">AR</span>
          <h2>Arquivos monitorados</h2>
          <p className="numero-grande">{dados?.qtd_arquivos ?? 0}</p>
          <p className="meta">com histórico salvo</p>
        </article>
        <article className="card resumo-card">
          <span className="resumo-icone">EX</span>
          <h2>Execução</h2>
          <p className="numero-grande">{dados?.ultima_execucao?.qtd_arquivos ?? 0}</p>
          <p className="meta">arquivos na última rodada</p>
        </article>
      </div>
    </div>
  );
}
