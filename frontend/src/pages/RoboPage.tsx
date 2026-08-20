import { type FormEvent, useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import {
  executarRoboSemEmail,
  listarExecucoes,
  obterAgendaRobo,
  obterLogExecucao,
  obterStatusRobo,
  salvarAgendaRobo,
} from "../api/leiautes";
import type {
  AgendaRobo,
  ExecucaoLogResponse,
  ExecucaoResumo,
  RoboStatusResponse,
} from "../api/types";

type AbaRobo = "log" | "agenda";

const DIAS = [
  { v: 0, label: "Seg" },
  { v: 1, label: "Ter" },
  { v: 2, label: "Qua" },
  { v: 3, label: "Qui" },
  { v: 4, label: "Sex" },
  { v: 5, label: "Sáb" },
  { v: 6, label: "Dom" },
];

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

function resumoDias(dias: number[]): string {
  if (!dias.length) return "—";
  const mapa = Object.fromEntries(DIAS.map((d) => [d.v, d.label]));
  return dias.map((d) => mapa[d] ?? String(d)).join(", ");
}

export default function RoboPage() {
  const [aba, setAba] = useState<AbaRobo>("log");
  const [status, setStatus] = useState<RoboStatusResponse | null>(null);
  const [execucoes, setExecucoes] = useState<ExecucaoResumo[]>([]);
  const [log, setLog] = useState<ExecucaoLogResponse | null>(null);
  const [agenda, setAgenda] = useState<AgendaRobo | null>(null);
  const [horariosTxt, setHorariosTxt] = useState("18:00");
  const [dias, setDias] = useState<number[]>([0, 1, 2, 3, 4]);
  const [roboAtivo, setRoboAtivo] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [executando, setExecutando] = useState(false);
  const [carregandoLog, setCarregandoLog] = useState(false);
  const [salvandoAgenda, setSalvandoAgenda] = useState(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const [statusResp, execResp, agendaResp] = await Promise.all([
        obterStatusRobo(),
        listarExecucoes(50, 0),
        obterAgendaRobo(),
      ]);
      setStatus(statusResp);
      setExecucoes(execResp.execucoes);
      setAgenda(agendaResp);
      setHorariosTxt((agendaResp.horarios || []).join(", ") || "18:00");
      setDias(agendaResp.dias_semana?.length ? agendaResp.dias_semana : [0, 1, 2, 3, 4]);
      setRoboAtivo(agendaResp.robo_ativo !== false);
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

  const toggleDia = (d: number) => {
    setDias((prev) =>
      prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d].sort(),
    );
  };

  const salvarAgenda = async (event: FormEvent) => {
    event.preventDefault();
    const horarios = horariosTxt
      .split(",")
      .map((h) => h.trim().slice(0, 5))
      .filter(Boolean);
    if (!horarios.length) {
      setErro("Informe pelo menos um horário (ex.: 18:00).");
      return;
    }
    if (!dias.length) {
      setErro("Selecione pelo menos um dia da semana.");
      return;
    }
    setSalvandoAgenda(true);
    setErro(null);
    setMensagem(null);
    try {
      const atualizada = await salvarAgendaRobo({
        horarios,
        dias_semana: dias,
        robo_ativo: roboAtivo,
        feriados: agenda?.feriados ?? [],
      });
      setAgenda(atualizada);
      setMensagem("Agenda salva. O cron do servidor passa a respeitar estes horários.");
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Erro ao salvar agenda.");
    } finally {
      setSalvandoAgenda(false);
    }
  };

  const ultima = status?.ultima_execucao ?? execucoes[0] ?? null;

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">Robô</h1>
          <p className="page-sub">
            Executar o monitoramento, consultar o log e definir a agenda automática.
          </p>
        </div>
        {aba === "log" && (
          <button
            type="button"
            className="btn-novo"
            disabled={executando || !status?.script_existe}
            onClick={() => void executar()}
          >
            {executando ? "Executando..." : "Executar agora"}
          </button>
        )}
      </div>

      <div className="admin-tabs config-abas" role="tablist">
        <button
          type="button"
          role="tab"
          className={aba === "log" ? "ativo" : ""}
          aria-selected={aba === "log"}
          onClick={() => setAba("log")}
        >
          Log
        </button>
        <button
          type="button"
          role="tab"
          className={aba === "agenda" ? "ativo" : ""}
          aria-selected={aba === "agenda"}
          onClick={() => setAba("agenda")}
        >
          Agenda
        </button>
      </div>

      {erro && <p className="erro">{erro}</p>}
      {mensagem && <p className="login-sucesso">{mensagem}</p>}

      {aba === "log" && (
        <>
          {ultima && (
            <p className="admin-ajuda">
              Última execução: <strong>#{ultima.id}</strong> ·{" "}
              <strong className={classeStatus(ultima.status)}>
                {rotuloStatus(ultima.status)}
              </strong>
              {ultima.status === "erro" && ultima.erro ? ` — ${ultima.erro}` : null}
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
        </>
      )}

      {aba === "agenda" && (
        <section className="config-painel-aba">
          <p className="admin-ajuda">
            O servidor consulta esta agenda a cada minuto. O robô principal só roda nos
            dias/horários abaixo. A garantia (17:30) continua no cron fixo e só avisa em
            falha.
          </p>
          <form className="admin-form" onSubmit={(e) => void salvarAgenda(e)}>
            <label className="admin-dia-chip">
              <input
                type="checkbox"
                checked={roboAtivo}
                onChange={(e) => setRoboAtivo(e.target.checked)}
              />
              Robô automático ligado
            </label>

            <label>
              <span className="field-label">Horários (HH:MM, separados por vírgula)</span>
              <input
                className="field-input"
                value={horariosTxt}
                onChange={(e) => setHorariosTxt(e.target.value)}
                placeholder="18:00"
              />
            </label>

            <div>
              <span className="field-label">Dias da semana</span>
              <div className="admin-dias">
                {DIAS.map((d) => (
                  <label key={d.v} className="admin-dia-chip">
                    <input
                      type="checkbox"
                      checked={dias.includes(d.v)}
                      onChange={() => toggleDia(d.v)}
                    />
                    {d.label}
                  </label>
                ))}
              </div>
            </div>

            {agenda && (
              <p className="meta">
                Atual:{" "}
                <strong className={agenda.robo_ativo ? "status-ok" : "status-erro"}>
                  {agenda.robo_ativo ? "Ligado" : "Desligado"}
                </strong>
                {" · "}
                {(agenda.horarios || []).join(", ") || "—"}
                {" · "}
                {resumoDias(agenda.dias_semana || [])}
              </p>
            )}

            <button type="submit" className="btn-novo" disabled={salvandoAgenda}>
              {salvandoAgenda ? "Salvando..." : "Salvar agenda"}
            </button>
          </form>
        </section>
      )}

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
