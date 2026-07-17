import { useEffect, useMemo, useState } from "react";
import { listarAlteracoes } from "../api/leiautes";
import type { AlteracaoResumo } from "../api/types";

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
  const [alteracoes, setAlteracoes] = useState<AlteracaoResumo[]>([]);
  const [selecionada, setSelecionada] = useState<AlteracaoResumo | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [filtroTexto, setFiltroTexto] = useState("");
  const [filtroLeiaute, setFiltroLeiaute] = useState("");
  const [filtroTipo, setFiltroTipo] = useState("");
  const [filtroStatus, setFiltroStatus] = useState("");

  useEffect(() => {
    setCarregando(true);
    listarAlteracoes()
      .then((resp) => {
        setAlteracoes(resp.alteracoes);
        setSelecionada(resp.alteracoes[0] ?? null);
      })
      .catch(() => setErro("API indisponível."))
      .finally(() => setCarregando(false));
  }, []);

  const vazia = alteracoes.length === 0;
  const resumoVazio = useMemo(
    () => ({
      id: 0,
      execucao_id: 0,
      leiaute_codigo: "SCD-4111",
      arquivo_nome: "Aguardando primeira alteração gravada",
      arquivo_tipo: "PDF",
      resumo_executivo:
        "Quando o robô comparar uma versão nova com a anterior, o resumo aparecerá aqui.",
      impacto_sugerido:
        "Sem impacto calculado ainda. Execute o robô após a migração da comparação.",
      status: "pendente",
      criado_em: "—",
      itens_incluidos: ["Itens incluídos serão listados aqui."],
      itens_removidos: ["Itens removidos serão listados aqui."],
      itens_alterados: ["Itens alterados serão listados aqui."],
    }),
    [],
  );
  const detalhe = selecionada ?? resumoVazio;
  const leiautes = Array.from(new Set(alteracoes.map((item) => item.leiaute_codigo).filter(Boolean)));
  const tipos = Array.from(new Set(alteracoes.map((item) => item.arquivo_tipo).filter(Boolean)));
  const status = Array.from(new Set(alteracoes.map((item) => item.status).filter(Boolean)));
  const filtradas = alteracoes.filter((item) => {
    const texto = `${item.leiaute_codigo} ${item.arquivo_nome} ${item.arquivo_tipo} ${item.resumo_executivo} ${item.itens_incluidos.join(" ")} ${item.itens_alterados.join(" ")} ${item.itens_removidos.join(" ")}`.toLowerCase();
    return (
      (!filtroTexto || texto.includes(filtroTexto.toLowerCase())) &&
      (!filtroLeiaute || item.leiaute_codigo === filtroLeiaute) &&
      (!filtroTipo || item.arquivo_tipo === filtroTipo) &&
      (!filtroStatus || item.status === filtroStatus)
    );
  });
  const itensRelatorio = vazia ? [resumoVazio] : filtradas;

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">Alterações</h1>
          <p className="page-sub">
            Histórico das diferenças entre a versão anterior e a versão atual.
          </p>
        </div>
        <button type="button" className="btn-novo">
          Exportar relatório
        </button>
      </div>

      {erro && <p className="erro">{erro}</p>}
      {carregando && <p className="meta">Carregando...</p>}
      {vazia && (
        <p className="admin-ajuda">
          Ainda não há alterações gravadas. A tela já está pronta para receber os
          dados quando o motor de comparação for conectado.
        </p>
      )}

      <section className="relatorio-filtros">
        <label>
          Buscar
          <input
            value={filtroTexto}
            onChange={(event) => setFiltroTexto(event.target.value)}
            placeholder="Arquivo, campo, prazo, evidência..."
          />
        </label>
        <label>
          Leiaute
          <select value={filtroLeiaute} onChange={(event) => setFiltroLeiaute(event.target.value)}>
            <option value="">Todos</option>
            {leiautes.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
        <label>
          Tipo
          <select value={filtroTipo} onChange={(event) => setFiltroTipo(event.target.value)}>
            <option value="">Todos</option>
            {tipos.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select value={filtroStatus} onChange={(event) => setFiltroStatus(event.target.value)}>
            <option value="">Todos</option>
            {status.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </label>
      </section>

      <div className="relatorio-layout">
        <section className="relatorio-lista">
          <div className="relatorio-lista-head">
            <strong>{itensRelatorio.length} registro(s)</strong>
            <span className="meta">Clique em uma linha para ver a evidência</span>
          </div>
          <div className="tabela-wrap">
            <table className="tabela">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Leiaute</th>
                  <th>Arquivo</th>
                  <th>Tipo</th>
                  <th>Resumo</th>
                </tr>
              </thead>
              <tbody>
                {itensRelatorio.map((item) => (
                  <tr
                    key={item.id}
                    className={detalhe.id === item.id ? "linha-ativa" : ""}
                    onClick={() => setSelecionada(item)}
                  >
                    <td>{formatarData(item.criado_em)}</td>
                    <td><strong>{item.leiaute_codigo || "Sem leiaute"}</strong></td>
                    <td>{item.arquivo_nome}</td>
                    <td><span className="tag">{item.arquivo_tipo}</span></td>
                    <td>{item.resumo_executivo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <article className="card detalhe-alteracao">
          <div className="page-cabecalho">
            <div>
              <h2>{detalhe.leiaute_codigo}</h2>
              <p className="meta">
                {detalhe.arquivo_nome} · {detalhe.arquivo_tipo} · {formatarData(detalhe.criado_em)}
              </p>
            </div>
            <span className={statusClasse(detalhe.status)}>{detalhe.status}</span>
          </div>

          <section className="detalhe-secao">
            <h3>Resumo executivo</h3>
            <p>{detalhe.resumo_executivo}</p>
          </section>
          <section className="detalhe-secao">
            <h3>Impacto sugerido</h3>
            <p>{detalhe.impacto_sugerido || "—"}</p>
          </section>

          <div className="diff-grid">
            <div>
              <h3>Inclusões com evidência</h3>
              <ul>
                {detalhe.itens_incluidos.map((item) => (
                  <li key={item}>{item}</li>
                ))}
                {detalhe.itens_incluidos.length === 0 && (
                  <li className="meta">Nenhuma inclusão identificada.</li>
                )}
              </ul>
            </div>
            <div>
              <h3>Alterações com evidência</h3>
              <ul>
                {detalhe.itens_alterados.map((item) => (
                  <li key={item}>{item}</li>
                ))}
                {detalhe.itens_alterados.length === 0 && (
                  <li className="meta">Nenhuma alteração de conteúdo identificada.</li>
                )}
              </ul>
            </div>
            <div>
              <h3>Remoções com evidência</h3>
              <ul>
                {detalhe.itens_removidos.map((item) => (
                  <li key={item}>{item}</li>
                ))}
                {detalhe.itens_removidos.length === 0 && (
                  <li className="meta">Nenhuma remoção identificada.</li>
                )}
              </ul>
            </div>
          </div>
        </article>
      </div>
    </div>
  );
}
