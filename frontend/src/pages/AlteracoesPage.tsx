import { useEffect, useMemo, useState } from "react";
import { listarAlteracoes } from "../api/leiautes";
import type { AlteracaoResumo } from "../api/types";

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

      <div className="alteracoes-layout">
        <div className="alteracoes-lista">
          {(vazia ? [resumoVazio] : alteracoes).map((item) => (
            <button
              key={item.id}
              type="button"
              className={`alteracao-card ${detalhe.id === item.id ? "ativo" : ""}`}
              onClick={() => setSelecionada(item)}
            >
              <strong>{item.leiaute_codigo || "Sem leiaute"}</strong>
              <span>{item.arquivo_nome}</span>
              <span className={`meta ${statusClasse(item.status)}`}>{item.status}</span>
            </button>
          ))}
        </div>

        <article className="card detalhe-alteracao">
          <div className="page-cabecalho">
            <div>
              <h2>{detalhe.leiaute_codigo}</h2>
              <p className="meta">
                {detalhe.arquivo_nome} · {detalhe.arquivo_tipo}
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
              <h3>Incluído</h3>
              <ul>
                {detalhe.itens_incluidos.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3>Alterado</h3>
              <ul>
                {detalhe.itens_alterados.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3>Removido</h3>
              <ul>
                {detalhe.itens_removidos.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </article>
      </div>
    </div>
  );
}
