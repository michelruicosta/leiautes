import { useCallback, useEffect, useMemo, useState } from "react";
import { listarAuditoria } from "../api/leiautes";
import type { LogAuditoria } from "../api/types";
import { ApiError } from "../api/client";
import CampoDataBr from "../components/CampoDataBr";
import { isoHoje, periodoPersonalizadoPadrao } from "../lib/datas";

const POR_PAGINA = 10;

const PAGINAS = [
  "Todas",
  "Cadastro de Leiautes",
  "Usuários e perfis",
  "Robô",
  "Configurações",
  "Alterar senha",
  "Login",
] as const;

const ACOES = [
  "Todas",
  "Criação",
  "Edição",
  "Exclusão",
  "Inativação",
  "Ativação",
  "Execução manual",
  "Autenticação",
  "Alterar senha",
  "Recuperação de senha",
] as const;

type Periodo = "todos" | "hoje" | "semana" | "mes" | "ano" | "personalizado";

function classeAcao(acao: string): string {
  const map: Record<string, string> = {
    Criação: "log-acao-criacao",
    Edição: "log-acao-edicao",
    Exclusão: "log-acao-exclusao",
    Inativação: "log-acao-inativacao",
    Ativação: "log-acao-ativacao",
    "Execução manual": "log-acao-execucao",
  };
  return map[acao] ?? "log-acao-outro";
}

function formatarQuando(iso: string): string {
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return iso;
  return data.toLocaleString("pt-BR", { hour12: false });
}

function periodoParaDatas(
  periodo: Periodo,
  personalizado: { de: string | null; ate: string | null },
) {
  const hoje = isoHoje();
  if (periodo === "todos") return { de: undefined, ate: undefined };
  if (periodo === "hoje") return { de: hoje, ate: hoje };
  if (periodo === "semana") {
    const d = new Date(`${hoje}T12:00:00`);
    d.setDate(d.getDate() - 7);
    return { de: d.toISOString().slice(0, 10), ate: hoje };
  }
  if (periodo === "mes") return { de: `${hoje.slice(0, 7)}-01`, ate: hoje };
  if (periodo === "ano") return { de: `${hoje.slice(0, 4)}-01-01`, ate: hoje };
  if (periodo === "personalizado" && personalizado.de && personalizado.ate) {
    return { de: personalizado.de, ate: personalizado.ate };
  }
  return null;
}

export default function AuditoriaPage() {
  const [registros, setRegistros] = useState<LogAuditoria[]>([]);
  const [total, setTotal] = useState(0);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [paginaAtual, setPaginaAtual] = useState(1);
  const [periodo, setPeriodo] = useState<Periodo>("todos");
  const [personalizado, setPersonalizado] = useState({
    deIso: "",
    ateIso: "",
    aplicado: false,
  });
  const [filtroPagina, setFiltroPagina] = useState("Todas");
  const [filtroAcao, setFiltroAcao] = useState("Todas");
  const [filtroUsuario, setFiltroUsuario] = useState("Todos");
  const [usuarios, setUsuarios] = useState<string[]>([]);

  const datas = useMemo(
    () =>
      periodoParaDatas(periodo, {
        de: personalizado.deIso || null,
        ate: personalizado.ateIso || null,
      }),
    [periodo, personalizado.deIso, personalizado.ateIso],
  );

  const carregar = useCallback(async () => {
    if (periodo === "personalizado" && !personalizado.aplicado) {
      setRegistros([]);
      setTotal(0);
      return;
    }
    setCarregando(true);
    setErro(null);
    try {
      const resp = await listarAuditoria({
        data_de: datas?.de,
        data_ate: datas?.ate,
        pagina: filtroPagina === "Todas" ? undefined : filtroPagina,
        acao: filtroAcao === "Todas" ? undefined : filtroAcao,
        usuario: filtroUsuario === "Todos" ? undefined : filtroUsuario,
        limit: 500,
      });
      setRegistros(resp.registros);
      setTotal(resp.total);
      setPaginaAtual(1);
      if (filtroUsuario === "Todos") {
        setUsuarios([...new Set(resp.registros.map((item) => item.usuario))].sort());
      }
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Erro ao carregar a trilha de auditoria.");
    } finally {
      setCarregando(false);
    }
  }, [periodo, personalizado.aplicado, datas, filtroPagina, filtroAcao, filtroUsuario]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const totalPaginas = Math.max(1, Math.ceil(registros.length / POR_PAGINA));
  const fatia = useMemo(
    () => registros.slice((paginaAtual - 1) * POR_PAGINA, paginaAtual * POR_PAGINA),
    [paginaAtual, registros],
  );

  const exportarCsv = () => {
    if (!registros.length) {
      setErro("Nenhum registro para exportar com os filtros atuais.");
      return;
    }
    const linhas = [
      ["Usuário", "Data / Hora", "Página", "Ação", "Detalhe"],
      ...registros.map((item) => [
        item.usuario,
        formatarQuando(item.criado_em),
        item.pagina,
        item.acao,
        item.detalhe,
      ]),
    ];
    const csv = linhas
      .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(";"))
      .join("\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `trilha-auditoria-${isoHoje()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">Trilha de auditoria</h1>
          <p className="page-sub">Quem fez o quê, quando e em qual tela.</p>
        </div>
        <button type="button" className="btn-novo" onClick={exportarCsv}>
          ⬇ Exportar CSV
        </button>
      </div>

      <p className="admin-ajuda">
        Cada criação, edição, inativação, ativação ou exclusão administrativa fica registrada
        com usuário, data, hora, tela e detalhe da ação.
      </p>

      {erro && <p className="erro">{erro}</p>}
      {carregando && <p className="meta">Carregando…</p>}

      <div className="filtros-periodo">
        {(
          [
            ["todos", "Todos"],
            ["hoje", "Hoje"],
            ["semana", "Esta semana"],
            ["mes", "Mês"],
            ["ano", "Ano"],
            ["personalizado", "Personalizado"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={periodo === id ? "ativo" : ""}
            onClick={() => {
              setPaginaAtual(1);
              if (id !== "personalizado") {
                setPeriodo(id);
                setPersonalizado((p) => ({ ...p, aplicado: false }));
                return;
              }
              if (periodo !== "personalizado") {
                const padrao = periodoPersonalizadoPadrao();
                setPersonalizado({
                  deIso: padrao.de,
                  ateIso: padrao.ate,
                  aplicado: false,
                });
              }
              setPeriodo("personalizado");
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {periodo === "personalizado" && (
        <div className="periodo-personalizado">
          <p className="periodo-personalizado-ajuda">
            Digite <strong>dd/mm/aaaa</strong> ou use o ícone do calendário, depois clique em{" "}
            <strong>Aplicar</strong>.
          </p>
          <div className="periodo-personalizado-campo">
            <CampoDataBr
              label="De"
              value={personalizado.deIso}
              onChange={(iso) =>
                setPersonalizado((p) => ({ ...p, deIso: iso, aplicado: false }))
              }
            />
          </div>
          <div className="periodo-personalizado-campo">
            <CampoDataBr
              label="Até"
              value={personalizado.ateIso}
              onChange={(iso) =>
                setPersonalizado((p) => ({ ...p, ateIso: iso, aplicado: false }))
              }
            />
          </div>
          <button
            type="button"
            className="btn-primary"
            onClick={() => {
              const { deIso, ateIso } = personalizado;
              if (!deIso || !ateIso) {
                alert("Informe as datas no formato dd/mm/aaaa.");
                return;
              }
              if (deIso > ateIso) {
                alert("A data De não pode ser maior que a data Até.");
                return;
              }
              setPersonalizado((p) => ({ ...p, aplicado: true }));
              setPaginaAtual(1);
            }}
          >
            Aplicar
          </button>
        </div>
      )}

      <section className="filtros-log">
        <div className="field">
          <label className="field-label">Página</label>
          <select
            className="field-input"
            value={filtroPagina}
            onChange={(event) => {
              setFiltroPagina(event.target.value);
              setPaginaAtual(1);
            }}
          >
            {PAGINAS.map((pagina) => (
              <option key={pagina} value={pagina}>
                {pagina}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label className="field-label">Ação</label>
          <select
            className="field-input"
            value={filtroAcao}
            onChange={(event) => {
              setFiltroAcao(event.target.value);
              setPaginaAtual(1);
            }}
          >
            {ACOES.map((acao) => (
              <option key={acao} value={acao}>
                {acao}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label className="field-label">Usuário</label>
          <select
            className="field-input"
            value={filtroUsuario}
            onChange={(event) => {
              setFiltroUsuario(event.target.value);
              setPaginaAtual(1);
            }}
          >
            <option value="Todos">Todos</option>
            {usuarios.map((usuario) => (
              <option key={usuario} value={usuario}>
                {usuario}
              </option>
            ))}
          </select>
        </div>
      </section>

      <p className="meta">
        {periodo === "personalizado" && !personalizado.aplicado
          ? "Selecione o período e clique em Aplicar."
          : `${total} registro(s) encontrado(s)`}
      </p>
      <div className="tabela-wrap">
        <table className="tabela">
          <thead>
            <tr>
              <th>Usuário</th>
              <th>Data / Hora</th>
              <th>Página</th>
              <th>Ação</th>
              <th>Detalhe</th>
            </tr>
          </thead>
          <tbody>
            {fatia.length === 0 ? (
              <tr>
                <td colSpan={5} className="meta">
                  Nenhum registro para os filtros selecionados.
                </td>
              </tr>
            ) : (
              fatia.map((item) => (
                <tr key={item.id}>
                  <td>{item.usuario}</td>
                  <td>{formatarQuando(item.criado_em)}</td>
                  <td>{item.pagina}</td>
                  <td>
                    <strong className={`log-acao ${classeAcao(item.acao)}`}>
                      {item.acao}
                    </strong>
                  </td>
                  <td>{item.detalhe}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        <div className="paginacao-log">
          <span>
            Página {paginaAtual} de {totalPaginas} — {registros.length} registro(s)
          </span>
          <div>
            <button
              type="button"
              disabled={paginaAtual <= 1}
              onClick={() => setPaginaAtual((p) => p - 1)}
            >
              ← Anterior
            </button>
            <button
              type="button"
              disabled={paginaAtual >= totalPaginas}
              onClick={() => setPaginaAtual((p) => p + 1)}
            >
              Próximo →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
