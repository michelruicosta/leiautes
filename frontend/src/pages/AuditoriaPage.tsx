import { useCallback, useEffect, useMemo, useState } from "react";
import { listarAuditoria } from "../api/leiautes";
import type { LogAuditoria } from "../api/types";

const PAGINAS = ["Todas", "Leiautes", "Usuários e perfis", "Robô", "Configurações"] as const;
const ACOES = [
  "Todas",
  "Criação",
  "Edição",
  "Exclusão",
  "Inativação",
  "Ativação",
  "Execução manual",
] as const;
const POR_PAGINA = 10;

function formatarQuando(iso: string): string {
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return iso;
  return data.toLocaleString("pt-BR", { hour12: false });
}

function hojeIso(): string {
  return new Date().toISOString().slice(0, 10);
}

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

export default function AuditoriaPage() {
  const [registros, setRegistros] = useState<LogAuditoria[]>([]);
  const [total, setTotal] = useState(0);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [paginaAtual, setPaginaAtual] = useState(1);
  const [filtroPagina, setFiltroPagina] = useState("Todas");
  const [filtroAcao, setFiltroAcao] = useState("Todas");
  const [dataDe, setDataDe] = useState("");
  const [dataAte, setDataAte] = useState("");

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const resp = await listarAuditoria({
        data_de: dataDe || undefined,
        data_ate: dataAte || undefined,
        pagina: filtroPagina === "Todas" ? undefined : filtroPagina,
        acao: filtroAcao === "Todas" ? undefined : filtroAcao,
        limit: 500,
      });
      setRegistros(resp.registros);
      setTotal(resp.total);
      setPaginaAtual(1);
    } catch {
      setErro("Erro ao carregar a trilha de auditoria.");
    } finally {
      setCarregando(false);
    }
  }, [dataAte, dataDe, filtroAcao, filtroPagina]);

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
    a.download = `trilha-auditoria-${hojeIso()}.csv`;
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
        <button type="button" className="btn-secondary" onClick={exportarCsv}>
          Exportar CSV
        </button>
      </div>

      <p className="admin-ajuda">
        Cada criação, edição, inativação, ativação ou exclusão administrativa fica registrada
        com usuário, data, hora, tela e detalhe da ação.
      </p>

      {erro && <p className="erro">{erro}</p>}
      {carregando && <p className="meta">Carregando...</p>}

      <section className="filtros-log">
        <label className="field">
          <span className="field-label">Data inicial</span>
          <input
            className="field-input"
            type="date"
            value={dataDe}
            onChange={(event) => setDataDe(event.target.value)}
          />
        </label>
        <label className="field">
          <span className="field-label">Data final</span>
          <input
            className="field-input"
            type="date"
            value={dataAte}
            onChange={(event) => setDataAte(event.target.value)}
          />
        </label>
        <label className="field">
          <span className="field-label">Página</span>
          <select
            className="field-input"
            value={filtroPagina}
            onChange={(event) => setFiltroPagina(event.target.value)}
          >
            {PAGINAS.map((pagina) => (
              <option key={pagina} value={pagina}>
                {pagina}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span className="field-label">Ação</span>
          <select
            className="field-input"
            value={filtroAcao}
            onChange={(event) => setFiltroAcao(event.target.value)}
          >
            {ACOES.map((acao) => (
              <option key={acao} value={acao}>
                {acao}
              </option>
            ))}
          </select>
        </label>
      </section>

      <p className="meta">{total} registro(s) encontrado(s)</p>
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
            Página {paginaAtual} de {totalPaginas} - {registros.length} registro(s)
          </span>
          <div>
            <button
              type="button"
              disabled={paginaAtual <= 1}
              onClick={() => setPaginaAtual((p) => p - 1)}
            >
              Anterior
            </button>
            <button
              type="button"
              disabled={paginaAtual >= totalPaginas}
              onClick={() => setPaginaAtual((p) => p + 1)}
            >
              Próximo
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
