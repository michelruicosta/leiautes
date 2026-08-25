import { useEffect, useMemo, useState } from "react";
import { obterDashboard } from "../api/leiautes";
import type { DashboardResponse } from "../api/types";

function formatarData(valor?: string | null): string {
  if (!valor) return "-";
  const data = new Date(valor);
  if (Number.isNaN(data.getTime())) return valor;
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(data);
}

function rotuloStatus(status?: string | null): string {
  const mapa: Record<string, string> = {
    sucesso: "Sucesso",
    erro: "Erro",
    em_andamento: "Em andamento",
  };
  return status ? mapa[status] ?? status : "Sem registro";
}

function classeStatus(status?: string | null): string {
  if (status === "sucesso") return "status-ok";
  if (status === "erro") return "status-erro";
  return "status-andamento";
}

export default function DashboardPage() {
  const [dados, setDados] = useState<DashboardResponse | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    obterDashboard().then(setDados).catch(() => setErro("API indisponível."));
  }, []);

  const totalRodada = useMemo(
    () => (dados?.qtd_entrou ?? 0) + (dados?.qtd_mudou ?? 0) + (dados?.qtd_saiu ?? 0),
    [dados],
  );
  const maiorDestaque = Math.max(
    1,
    ...(dados?.arquivos_destaque ?? []).map((item) => item.total_evidencias),
  );

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">Monitoramento</h1>
          <p className="page-sub">Visão da última rodada e do que mudou nos leiautes Bacen.</p>
        </div>
      </div>

      {erro && <p className="erro">{erro}</p>}

      <section className="dashboard-executivo">
        <div>
          <span className="dashboard-eyebrow">Última execução</span>
          <h2>{formatarData(dados?.ultima_execucao?.iniciado_em)}</h2>
          <div className="dashboard-meta-row">
            <strong className={classeStatus(dados?.ultima_execucao?.status)}>
              {rotuloStatus(dados?.ultima_execucao?.status)}
            </strong>
            <span>{dados?.ultima_execucao?.qtd_arquivos ?? 0} arquivos processados</span>
            <span>{dados?.qtd_leiautes ?? 0} leiaute(s) ativo(s)</span>
          </div>
        </div>
        <div className="dashboard-total">
          <span>{totalRodada}</span>
          <p>evidências na última execução</p>
        </div>
      </section>

      <section className="dashboard-change-grid">
        <article className="dashboard-change-card dashboard-change-entrou">
          <span>Entrou</span>
          <strong>{dados?.qtd_entrou ?? 0}</strong>
          <p>novos trechos, campos ou arquivos identificados</p>
        </article>
        <article className="dashboard-change-card dashboard-change-mudou">
          <span>Mudou</span>
          <strong>{dados?.qtd_mudou ?? 0}</strong>
          <p>itens com antes e depois para revisão</p>
        </article>
        <article className="dashboard-change-card dashboard-change-saiu">
          <span>Saiu</span>
          <strong>{dados?.qtd_saiu ?? 0}</strong>
          <p>conteúdos removidos em relação à versão anterior</p>
        </article>
      </section>

      <section className="dashboard-ranking">
        <div className="tabela-cabecalho">
          <div>
            <h2>Arquivos mais relevantes</h2>
            <p className="meta">
              Priorização por volume de evidências encontradas na última execução.
            </p>
          </div>
          <p className="meta">{dados?.qtd_arquivos ?? 0} arquivos monitorados</p>
        </div>

        <div className="tabela-wrap">
          <table className="tabela dashboard-table">
            <thead>
              <tr>
                <th>Leiaute</th>
                <th>Arquivo mais relevante</th>
                <th>Tipo</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              {(dados?.arquivos_destaque ?? []).length === 0 ? (
                <tr>
                  <td colSpan={4} className="meta">
                    Nenhuma alteração encontrada na última execução.
                  </td>
                </tr>
              ) : (
                dados?.arquivos_destaque.map((item) => (
                  <tr key={`${item.leiaute_codigo}-${item.arquivo_nome}`}>
                    <td>
                      <strong>{item.leiaute_codigo}</strong>
                    </td>
                    <td>{item.arquivo_nome}</td>
                    <td>
                      <span className="tag">{item.arquivo_tipo}</span>
                    </td>
                    <td>
                      <strong>{item.total_evidencias} evidências</strong>
                      <div className="dashboard-bar">
                        <span
                          style={{
                            width: `${Math.max(
                              8,
                              Math.round((item.total_evidencias / maiorDestaque) * 100),
                            )}%`,
                          }}
                        />
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
