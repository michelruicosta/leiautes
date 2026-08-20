import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import {
  executarRoboSemEmail,
  listarExecucoes,
  obterLogExecucao,
  obterStatusRobo,
} from "../api/leiautes";
import type {
  ExecucaoLogResponse,
  ExecucaoResumo,
  RoboStatusResponse,
} from "../api/types";

function formatarData(iso?: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("pt-BR", { hour12: false });
  } catch {
    return iso;
  }
}

function classeStatus(status: string): string {
  if (status === "sucesso") return "status-ok";
  if (status === "erro") return "status-erro";
  return "status-andamento";
}

function rotuloStatus(status: string): string {
  const mapa: Record<string, string> = {
    em_andamento: "Em andamento",
    sucesso: "Sucesso",
    erro: "Erro",
  };
  return mapa[status] ?? status;
}

function textoErro(execucao: ExecucaoResumo): string {
  if (execucao.status === "sucesso") return "—";
  const msg = (execucao.erro || "").trim();
  if (msg) return msg;
  if (execucao.status === "erro") return "Falha sem detalhe registrado. Abra o log.";
  if (execucao.status === "em_andamento") return "Em andamento…";
  return "—";
}

export default function RoboPage() {
  const [status, setStatus] = useState<RoboStatusResponse | null>(null);
  const [execucoes, setExecucoes] = useState<ExecucaoResumo[]>([]);
  const [log, setLog] = useState<ExecucaoLogResponse | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [executando, setExecutando] = useState(false);
  const [carregandoLog, setCarregandoLog] = useState(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const [statusResp, execResp] = await Promise.all([
        obterStatusRobo(),
        listarExecucoes(50, 0),
      ]);
      setStatus(statusResp);
      setExecucoes(execResp.execucoes);
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "API indisponível.");
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const executar = async () => {
    setExecutando(true);
    setErro(null);
    setMensagem(null);
    try {
      const resposta = await executarRoboSemEmail();
      setMensagem(
        `Execução #${resposta.execucao_id} finalizada: ${rotuloStatus(
          resposta.status,
        ).toLowerCase()}.`,
      );
      await carregar();
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Erro ao executar robô.");
    } finally {
      setExecutando(false);
    }
  };

  const abrirLog = async (execucao: ExecucaoResumo) => {
    setCarregandoLog(true);
    setErro(null);
    try {
      setLog(await obterLogExecucao(execucao.id));
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Erro ao carregar log.");
    } finally {
      setCarregandoLog(false);
    }
  };

  const ultima = status?.ultima_execucao ?? execucoes[0] ?? null;

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">Robô</h1>
          <p className="page-sub">
            Executar o monitoramento e consultar o log (sucesso, erro e motivo).
          </p>
        </div>
        <button
          type="button"
          className="btn-novo"
          disabled={executando || !status?.script_existe}
          onClick={() => void executar()}
        >
          {executando ? "Executando..." : "Executar agora"}
        </button>
      </div>

      {erro && <p className="erro">{erro}</p>}
      {mensagem && <p className="login-sucesso">{mensagem}</p>}

      {ultima && (
        <p className="admin-ajuda">
          Última execução: <strong>#{ultima.id}</strong> ·{" "}
          <strong className={classeStatus(ultima.status)}>
            {rotuloStatus(ultima.status)}
          </strong>
          {ultima.status === "erro" && ultima.erro
            ? ` — ${ultima.erro}`
            : null}
        </p>
      )}

      <section className="card">
        <div className="tabela-cabecalho">
          <div>
            <h2>Log de execução</h2>
            <p className="meta">
              Consulta do que o robô detectou fica em Histórico e Versões.
            </p>
          </div>
          {carregando && <span className="meta">Carregando...</span>}
        </div>

        <div className="tabela-wrap">
          <table className="tabela">
            <thead>
              <tr>
                <th>Execução</th>
                <th>Início</th>
                <th>Fim</th>
                <th>Status</th>
                <th>Erro / motivo</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {execucoes.length === 0 ? (
                <tr>
                  <td colSpan={6} className="meta">
                    Nenhuma execução registrada ainda.
                  </td>
                </tr>
              ) : (
                execucoes.map((execucao) => (
                  <tr key={execucao.id}>
                    <td>
                      <strong>#{execucao.id}</strong>
                    </td>
                    <td>{formatarData(execucao.iniciado_em)}</td>
                    <td>{formatarData(execucao.finalizado_em)}</td>
                    <td>
                      <strong className={classeStatus(execucao.status)}>
                        {rotuloStatus(execucao.status)}
                      </strong>
                    </td>
                    <td className="resumo-cel">{textoErro(execucao)}</td>
                    <td>
                      <button
                        type="button"
                        className="btn-detalhes"
                        disabled={carregandoLog}
                        onClick={() => void abrirLog(execucao)}
                      >
                        Ver log
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {log && (
        <div className="modal-backdrop" onClick={() => setLog(null)}>
          <section
            className="modal-detalhe modal-log"
            role="dialog"
            aria-modal="true"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-detalhe-head">
              <div>
                <h2>Log da execução #{log.execucao.id}</h2>
                <p className="meta">
                  {formatarData(log.execucao.iniciado_em)} até{" "}
                  {formatarData(log.execucao.finalizado_em)} ·{" "}
                  <strong className={classeStatus(log.execucao.status)}>
                    {rotuloStatus(log.execucao.status)}
                  </strong>
                </p>
                {log.execucao.erro && (
                  <p className="erro" style={{ marginTop: "0.5rem" }}>
                    {log.execucao.erro}
                  </p>
                )}
              </div>
              <button
                type="button"
                className="modal-fechar"
                aria-label="Fechar"
                onClick={() => setLog(null)}
              >
                ×
              </button>
            </div>
            <div className="modal-log-body">
              {!log.disponivel && (
                <p className="admin-ajuda">
                  Sem arquivo de log salvo. Exibindo a observação registrada no
                  histórico.
                </p>
              )}
              <pre className="log-output">{log.log_texto}</pre>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
