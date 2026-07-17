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
  if (!iso) return "-";
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
        `Execução ${resposta.execucao_id} finalizada com status ${rotuloStatus(
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

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">Robô</h1>
          <p className="page-sub">Execução manual, status e histórico operacional.</p>
        </div>
        <button
          type="button"
          className="btn-novo"
          disabled={executando || !status?.script_existe}
          onClick={() => void executar()}
        >
          {executando ? "Executando..." : "Executar sem e-mail"}
        </button>
      </div>

      {erro && <p className="erro">{erro}</p>}
      {mensagem && <p className="login-sucesso">{mensagem}</p>}

      <section className="card robo-status-card">
        <div>
          <h2>Status do motor</h2>
          <p className="meta">{status?.script_motor ?? "-"}</p>
          <p className={status?.script_existe ? "status-ok" : "status-erro"}>
            {status?.script_existe ? "Script encontrado" : "Script não encontrado"}
          </p>
        </div>
        <p className="admin-ajuda">
          Por padrão, a execução manual do app roda com envio de e-mail desativado. Quando
          liberado, o envio fica redirecionado para michel@finaud.com.br.
        </p>
      </section>

      <section className="card">
        <div className="tabela-cabecalho">
          <div>
            <h2>Log de execução do robô</h2>
            <p className="meta">
              Histórico das execuções do monitoramento Bacen, da mais recente para a mais antiga.
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
                <th>Leiautes</th>
                <th>Arquivos</th>
                <th>Alterações</th>
                <th>E-mails</th>
                <th>Observação</th>
                <th>Ação</th>
              </tr>
            </thead>
            <tbody>
              {execucoes.length === 0 ? (
                <tr>
                  <td colSpan={10} className="meta">
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
                    <td>{execucao.qtd_leiautes}</td>
                    <td>{execucao.qtd_arquivos}</td>
                    <td>{execucao.qtd_alteracoes}</td>
                    <td>{execucao.emails_enviados}</td>
                    <td className="resumo-cel">{execucao.erro ?? "-"}</td>
                    <td>
                      <button
                        type="button"
                        className="btn-secondary"
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
                  {rotuloStatus(log.execucao.status)}
                </p>
                <p className="meta">{log.log_path ?? "Sem arquivo físico associado."}</p>
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
                  Esta execução não possui arquivo de log salvo. Abaixo está a observação
                  registrada no histórico.
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
