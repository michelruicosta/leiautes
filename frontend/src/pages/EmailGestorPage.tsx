import { useEffect, useState } from "react";
import { DiffEvidenceList } from "../components/DiffEvidence";
import { obterPreviewEmailGestor } from "../api/leiautes";
import type { AlteracaoResumo, EmailGestorPreviewResponse } from "../api/types";

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
        <DiffEvidenceList
          titulo="Entrou"
          tipo="incluido"
          itens={alteracao.itens_incluidos}
        />
        <DiffEvidenceList
          titulo="Mudou"
          tipo="alterado"
          itens={alteracao.itens_alterados}
        />
        <DiffEvidenceList
          titulo="Saiu"
          tipo="removido"
          itens={alteracao.itens_removidos}
        />
      </div>
    </article>
  );
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
