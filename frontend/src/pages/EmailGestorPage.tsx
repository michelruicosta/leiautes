import { useEffect, useState } from "react";
import EmailGestorTemplate from "../components/EmailGestorTemplate";
import { obterPreviewEmailGestor } from "../api/leiautes";
import type { EmailGestorPreviewResponse } from "../api/types";

function formatarDataRef(preview: EmailGestorPreviewResponse | null): string {
  const iso = preview?.alteracoes?.[0]?.criado_em;
  if (iso) {
    const d = new Date(iso);
    if (!Number.isNaN(d.getTime())) {
      return d.toLocaleDateString("pt-BR");
    }
  }
  return new Date().toLocaleDateString("pt-BR");
}

export default function EmailGestorPage() {
  const [preview, setPreview] = useState<EmailGestorPreviewResponse | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  const carregar = (mostrarMensagem = true) => {
    setCarregando(true);
    setErro(null);
    setMsg(null);
    obterPreviewEmailGestor()
      .then((resp) => {
        setPreview(resp);
        if (mostrarMensagem) setMsg("Prévia atualizada.");
      })
      .catch(() => setErro("API indisponível."))
      .finally(() => setCarregando(false));
  };

  useEffect(() => {
    carregar(false);
  }, []);

  const dataRef = formatarDataRef(preview);

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">E-mail do gestor</h1>
          <p className="page-sub">
            Prévia do comunicado no mesmo layout do e-mail enviado ao gestor.
          </p>
        </div>
        <div className="admin-acoes">
          <button
            type="button"
            className="btn-secondary"
            disabled={carregando}
            onClick={() => carregar(true)}
          >
            {carregando ? "Atualizando..." : "Atualizar prévia"}
          </button>
          <button
            type="button"
            className="btn-novo"
            disabled
            title="O envio real será liberado após validação das configurações SMTP."
          >
            Envio real pendente
          </button>
        </div>
      </div>

      {erro && <p className="erro">{erro}</p>}
      {msg && !carregando && <p className="login-sucesso">{msg}</p>}
      {carregando && <p className="meta">Carregando...</p>}

      <div className="email-preview">
        <div className="email-preview-head">
          <strong>Assunto</strong>
          <span>{preview?.assunto ?? `Atualização em leiautes Bacen - ${dataRef}`}</span>
          <span className="meta">
            Para: {preview?.destinatarios.join(", ") || "destinatários não configurados"}
          </span>
          {preview?.copia.length ? (
            <span className="meta">Cc: {preview.copia.join(", ")}</span>
          ) : null}
        </div>
        <div className="email-preview-body email-preview-body-tpl">
          <EmailGestorTemplate
            dataRef={dataRef}
            alteracoes={preview?.alteracoes ?? []}
          />
          {(preview?.anexos?.length ?? 0) > 0 ? (
            <p className="email-tpl-anexos">
              Anexos: {preview?.anexos.join(", ")}
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
