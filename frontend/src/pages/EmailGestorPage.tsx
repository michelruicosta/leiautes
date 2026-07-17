import { useEffect, useState } from "react";
import { obterPreviewEmailGestor } from "../api/leiautes";
import type { AlteracaoResumo, EmailGestorPreviewResponse } from "../api/types";

function ListaDiferencas({
  titulo,
  itens,
  vazio,
}: {
  titulo: string;
  itens: string[];
  vazio: string;
}) {
  return (
    <section className="email-diff-bloco">
      <h3>{titulo}</h3>
      {itens.length ? (
        <ul>
          {itens.map((item, index) => (
            <li key={`${titulo}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="meta">{vazio}</p>
      )}
    </section>
  );
}

function AlteracaoEmailCard({ alteracao }: { alteracao: AlteracaoResumo }) {
  return (
    <article className="email-alteracao">
      <header>
        <h2>
          {alteracao.leiaute_codigo} · {alteracao.arquivo_nome}
        </h2>
        <span className="meta">{alteracao.arquivo_tipo}</span>
      </header>
      <p>{alteracao.resumo_executivo}</p>
      <p className="meta">{alteracao.impacto_sugerido}</p>
      <div className="email-diff-grid">
        <ListaDiferencas
          titulo="Inclusões"
          itens={alteracao.itens_incluidos}
          vazio="Nenhuma inclusão identificada."
        />
        <ListaDiferencas
          titulo="Alterações"
          itens={alteracao.itens_alterados}
          vazio="Nenhuma alteração de conteúdo identificada."
        />
        <ListaDiferencas
          titulo="Remoções"
          itens={alteracao.itens_removidos}
          vazio="Nenhuma remoção identificada."
        />
      </div>
    </article>
  );
}

export default function EmailGestorPage() {
  const [preview, setPreview] = useState<EmailGestorPreviewResponse | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  useEffect(() => {
    setCarregando(true);
    obterPreviewEmailGestor()
      .then(setPreview)
      .catch(() => setErro("API indisponível."))
      .finally(() => setCarregando(false));
  }, []);

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">E-mail do gestor</h1>
          <p className="page-sub">
            Prévia do comunicado com resumo executivo das diferenças.
          </p>
        </div>
        <div className="admin-acoes">
          <button type="button" className="btn-secondary">
            Atualizar prévia
          </button>
          <button type="button" className="btn-novo">
            Enviar
          </button>
        </div>
      </div>

      {erro && <p className="erro">{erro}</p>}
      {carregando && <p className="meta">Carregando...</p>}

      <div className="email-preview">
        <div className="email-preview-head">
          <strong>Assunto</strong>
          <span>{preview?.assunto ?? "Atualização em leiautes Bacen - {data}"}</span>
          <span className="meta">
            Para: {preview?.destinatarios.join(", ") || "destinatários não configurados"}
          </span>
          {preview?.copia.length ? (
            <span className="meta">Cc: {preview.copia.join(", ")}</span>
          ) : null}
        </div>
        <div className="email-preview-body">
          <p>{preview?.resumo ?? "Prévia ainda não carregada."}</p>
          {(preview?.alteracoes ?? []).length === 0 ? (
            <p className="admin-ajuda">
              Nenhuma alteração registrada ainda. Após a comparação real, esta área
              exibirá o resumo por leiaute e os itens incluídos, removidos e alterados.
            </p>
          ) : (
            preview?.alteracoes.map((alt) => (
              <AlteracaoEmailCard key={alt.id} alteracao={alt} />
            ))
          )}
          <p className="meta">
            Anexos: {preview?.anexos.join(", ") || "nenhum anexo selecionado"}
          </p>
        </div>
      </div>
    </div>
  );
}
