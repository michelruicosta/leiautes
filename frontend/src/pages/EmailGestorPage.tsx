import { useEffect, useState } from "react";
import { obterPreviewEmailGestor } from "../api/leiautes";
import type { EmailGestorPreviewResponse } from "../api/types";

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
              <article key={alt.id} className="card">
                <h2>
                  {alt.leiaute_codigo} · {alt.arquivo_nome}
                </h2>
                <p>{alt.resumo_executivo}</p>
                <p className="meta">{alt.impacto_sugerido}</p>
              </article>
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
