import { useEffect, useMemo, useState } from "react";
import { DiffEvidenceList } from "../components/DiffEvidence";
import {
  baixarRelatorioAlteracoes,
  baixarVersaoArquivo,
  listarAlteracoes,
  listarVersoesArquivos,
} from "../api/leiautes";
import type { AlteracaoResumo, VersaoArquivoResumo } from "../api/types";

type AbaHistorico = "historico" | "versoes";

function formatarData(valor: string): string {
  const data = new Date(valor);
  if (Number.isNaN(data.getTime())) return valor;
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(data);
}

function statusClasse(status: string): string {
  if (status === "enviado") return "status-ok";
  if (status === "erro") return "status-erro";
  return "status-andamento";
}

export default function AlteracoesPage() {
  const [aba, setAba] = useState<AbaHistorico>("historico");
  const [alteracoes, setAlteracoes] = useState<AlteracaoResumo[]>([]);
  const [versoes, setVersoes] = useState<VersaoArquivoResumo[]>([]);
  const [selecionada, setSelecionada] = useState<AlteracaoResumo | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [carregandoVersoes, setCarregandoVersoes] = useState(false);
  const [filtroTexto, setFiltroTexto] = useState("");
  const [filtroLeiaute, setFiltroLeiaute] = useState("");
  const [filtroTipo, setFiltroTipo] = useState("");
  const [filtroTextoVersoes, setFiltroTextoVersoes] = useState("");
  const [filtroLeiauteVersoes, setFiltroLeiauteVersoes] = useState("");
  const [filtroTipoVersoes, setFiltroTipoVersoes] = useState("");
  const [baixando, setBaixando] = useState(false);
  const [baixandoVersaoId, setBaixandoVersaoId] = useState<number | null>(null);

  useEffect(() => {
    setCarregando(true);
    listarAlteracoes()
      .then((resp) => {
        setAlteracoes(resp.alteracoes);
        setSelecionada(null);
      })
      .catch(() => setErro("API indisponível."))
      .finally(() => setCarregando(false));
  }, []);

  useEffect(() => {
    if (aba !== "versoes") return;
    setCarregandoVersoes(true);
    setErro(null);
    listarVersoesArquivos()
      .then((resp) => setVersoes(resp.versoes))
      .catch(() => setErro("Não foi possível carregar as versões guardadas."))
      .finally(() => setCarregandoVersoes(false));
  }, [aba]);

  const vazia = alteracoes.length === 0;
  const resumoVazio = useMemo(
    () => ({
      id: 0,
      execucao_id: 0,
      leiaute_codigo: "—",
      arquivo_nome: "Aguardando primeira alteração gravada",
      arquivo_tipo: "—",
      resumo_executivo:
        "Quando o robô detectar uma mudança, o registro aparecerá aqui.",
      impacto_sugerido: "—",
      status: "pendente",
      criado_em: "—",
      itens_incluidos: [] as string[],
      itens_removidos: [] as string[],
      itens_alterados: [] as string[],
    }),
    [],
  );
  const detalhe = selecionada;
  const leiautes = Array.from(
    new Set(alteracoes.map((item) => item.leiaute_codigo).filter(Boolean)),
  );
  const tipos = Array.from(
    new Set(alteracoes.map((item) => item.arquivo_tipo).filter(Boolean)),
  );
  const filtradas = alteracoes.filter((item) => {
    const texto =
      `${item.leiaute_codigo} ${item.arquivo_nome} ${item.arquivo_tipo} ${item.resumo_executivo} ${item.itens_incluidos.join(" ")} ${item.itens_alterados.join(" ")} ${item.itens_removidos.join(" ")}`.toLowerCase();
    return (
      (!filtroTexto || texto.includes(filtroTexto.toLowerCase())) &&
      (!filtroLeiaute || item.leiaute_codigo === filtroLeiaute) &&
      (!filtroTipo || item.arquivo_tipo === filtroTipo)
    );
  });
  const itensRelatorio = vazia ? [resumoVazio] : filtradas;

  const leiautesVersoes = Array.from(
    new Set(versoes.map((item) => item.leiaute_codigo).filter(Boolean)),
  );
  const tiposVersoes = Array.from(
    new Set(versoes.map((item) => item.arquivo_tipo).filter(Boolean)),
  );
  const versoesFiltradas = versoes.filter((item) => {
    const texto =
      `${item.leiaute_codigo} ${item.arquivo_nome} ${item.arquivo_tipo} ${item.vigencia}`.toLowerCase();
    return (
      (!filtroTextoVersoes || texto.includes(filtroTextoVersoes.toLowerCase())) &&
      (!filtroLeiauteVersoes || item.leiaute_codigo === filtroLeiauteVersoes) &&
      (!filtroTipoVersoes || item.arquivo_tipo === filtroTipoVersoes)
    );
  });

  const exportarHistorico = async () => {
    setErro(null);
    setBaixando(true);
    try {
      await baixarRelatorioAlteracoes("historico");
    } catch {
      setErro("Não foi possível exportar o histórico.");
    } finally {
      setBaixando(false);
    }
  };

  const baixarVersao = async (item: VersaoArquivoResumo) => {
    setErro(null);
    setBaixandoVersaoId(item.id);
    try {
      await baixarVersaoArquivo(item.id, item.arquivo_nome);
    } catch {
      setErro("Não foi possível baixar o arquivo.");
    } finally {
      setBaixandoVersaoId(null);
    }
  };

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">Histórico e Versões</h1>
          <p className="page-sub">
            Consultar o que o robô detectou e baixar arquivos guardados.
          </p>
        </div>
        {aba === "historico" && (
          <div className="acoes-relatorio">
            <button
              className="btn-novo"
              disabled={baixando}
              type="button"
              onClick={() => void exportarHistorico()}
            >
              {baixando ? "Gerando..." : "Exportar"}
            </button>
          </div>
        )}
      </div>

      <div className="admin-tabs config-abas" role="tablist">
        <button
          type="button"
          role="tab"
          className={aba === "historico" ? "ativo" : ""}
          aria-selected={aba === "historico"}
          onClick={() => setAba("historico")}
        >
          Histórico
        </button>
        <button
          type="button"
          role="tab"
          className={aba === "versoes" ? "ativo" : ""}
          aria-selected={aba === "versoes"}
          onClick={() => setAba("versoes")}
        >
          Versões de Arquivos
        </button>
      </div>

      {erro && <p className="erro">{erro}</p>}
      {carregando && aba === "historico" && <p className="meta">Carregando...</p>}
      {carregandoVersoes && aba === "versoes" && (
        <p className="meta">Carregando versões...</p>
      )}

      {aba === "historico" && (
        <>
          {vazia && (
            <p className="admin-ajuda">
              Ainda não há alterações gravadas. Quando o robô detectar mudanças,
              elas aparecerão nesta lista.
            </p>
          )}

          <section className="relatorio-filtros">
            <label>
              Buscar
              <input
                value={filtroTexto}
                onChange={(event) => setFiltroTexto(event.target.value)}
                placeholder="Arquivo, leiaute, evidência..."
              />
            </label>
            <label>
              Leiaute
              <select
                value={filtroLeiaute}
                onChange={(event) => setFiltroLeiaute(event.target.value)}
              >
                <option value="">Todos</option>
                {leiautes.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Tipo
              <select
                value={filtroTipo}
                onChange={(event) => setFiltroTipo(event.target.value)}
              >
                <option value="">Todos</option>
                {tipos.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
          </section>

          <div className="relatorio-layout relatorio-layout-lista relatorio-layout-sem-detalhe">
            <section className="relatorio-lista">
              <div className="relatorio-lista-head">
                <strong>{itensRelatorio.length} registro(s)</strong>
                <span className="meta">
                  Use Alterações para ver as evidências na tela
                </span>
              </div>
              <div className="tabela-wrap">
                <table className="tabela tabela-registros">
                  <thead>
                    <tr>
                      <th>Data</th>
                      <th>Leiaute</th>
                      <th>Arquivo</th>
                      <th>Tipo</th>
                      <th>Resumo</th>
                      <th>Alterações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {itensRelatorio.map((item) => (
                      <tr
                        key={item.id}
                        className={detalhe?.id === item.id ? "linha-ativa" : ""}
                      >
                        <td>{formatarData(item.criado_em)}</td>
                        <td>
                          <strong>{item.leiaute_codigo || "Sem leiaute"}</strong>
                        </td>
                        <td>{item.arquivo_nome}</td>
                        <td>
                          <span className="tag">{item.arquivo_tipo}</span>
                        </td>
                        <td>{item.resumo_executivo}</td>
                        <td>
                          {!vazia && (
                            <button
                              type="button"
                              className="btn-detalhes"
                              onClick={() => setSelecionada(item)}
                            >
                              Detalhes
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        </>
      )}

      {aba === "versoes" && (
        <>
          <section className="relatorio-filtros">
            <label>
              Buscar
              <input
                value={filtroTextoVersoes}
                onChange={(event) => setFiltroTextoVersoes(event.target.value)}
                placeholder="Arquivo, leiaute, vigência..."
              />
            </label>
            <label>
              Leiaute
              <select
                value={filtroLeiauteVersoes}
                onChange={(event) => setFiltroLeiauteVersoes(event.target.value)}
              >
                <option value="">Todos</option>
                {leiautesVersoes.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Tipo
              <select
                value={filtroTipoVersoes}
                onChange={(event) => setFiltroTipoVersoes(event.target.value)}
              >
                <option value="">Todos</option>
                {tiposVersoes.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
          </section>

          <div className="relatorio-layout relatorio-layout-lista relatorio-layout-sem-detalhe">
            <section className="relatorio-lista">
              <div className="relatorio-lista-head">
                <strong>{versoesFiltradas.length} arquivo(s)</strong>
                <span className="meta">Download da cópia guardada no servidor</span>
              </div>
              <div className="tabela-wrap">
                <table className="tabela tabela-registros">
                  <thead>
                    <tr>
                      <th>Capturado em</th>
                      <th>Leiaute</th>
                      <th>Arquivo</th>
                      <th>Vigência</th>
                      <th>Tipo</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {versoesFiltradas.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="meta">
                          Nenhum arquivo guardado encontrado.
                        </td>
                      </tr>
                    ) : (
                      versoesFiltradas.map((item) => (
                        <tr key={item.id}>
                          <td>{formatarData(item.capturado_em)}</td>
                          <td>
                            <strong>{item.leiaute_codigo || "Sem leiaute"}</strong>
                          </td>
                          <td>
                            <span className="arquivo-com-badge">
                              {item.arquivo_nome}
                              {item.fora_do_site && (
                                <span className="badge-fora-site" title="Não está mais no site do Bacen; a cópia local permanece disponível">
                                  Fora do site
                                </span>
                              )}
                            </span>
                          </td>
                          <td>{item.vigencia || "—"}</td>
                          <td>
                            <span className="tag">{item.arquivo_tipo}</span>
                          </td>
                          <td>
                            <button
                              type="button"
                              className="btn-detalhes"
                              disabled={baixandoVersaoId === item.id}
                              onClick={() => void baixarVersao(item)}
                            >
                              {baixandoVersaoId === item.id
                                ? "Baixando..."
                                : "Download"}
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        </>
      )}

      {detalhe && (
        <div
          className="modal-backdrop"
          role="presentation"
          onClick={() => setSelecionada(null)}
        >
          <article
            className="modal-detalhe"
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-alteracao-titulo"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="modal-detalhe-head">
              <div>
                <h2 id="modal-alteracao-titulo">{detalhe.leiaute_codigo}</h2>
                <p className="meta">
                  {detalhe.arquivo_nome} · {detalhe.arquivo_tipo} ·{" "}
                  {formatarData(detalhe.criado_em)}
                </p>
              </div>
              <div className="modal-detalhe-acoes">
                <span className={statusClasse(detalhe.status)}>
                  {detalhe.status}
                </span>
                <button
                  type="button"
                  className="modal-fechar"
                  aria-label="Fechar detalhes"
                  onClick={() => setSelecionada(null)}
                >
                  ×
                </button>
              </div>
            </header>

            <div className="modal-detalhe-body">
              <section className="modal-resumo-grid">
                <div>
                  <h3>Resumo executivo</h3>
                  <p>{detalhe.resumo_executivo}</p>
                </div>
                <div>
                  <h3>Impacto sugerido</h3>
                  <p>{detalhe.impacto_sugerido || "—"}</p>
                </div>
              </section>

              <section className="modal-evidencias">
                <h3>Evidências</h3>
                <div className="diff-grid modal-diff-grid">
                  <DiffEvidenceList
                    titulo="Entrou"
                    tipo="incluido"
                    itens={detalhe.itens_incluidos}
                  />
                  <DiffEvidenceList
                    titulo="Mudou"
                    tipo="alterado"
                    itens={detalhe.itens_alterados}
                  />
                  <DiffEvidenceList
                    titulo="Saiu"
                    tipo="removido"
                    itens={detalhe.itens_removidos}
                  />
                </div>
              </section>
            </div>
          </article>
        </div>
      )}
    </div>
  );
}
