import { useEffect, useState } from "react";

export type ConfirmacaoConfig = {
  titulo: string;
  texto: string;
  rotuloOk: string;
  perigo?: boolean;
  exigirDigitacao?: string;
  onConfirm: () => void | Promise<void>;
  onCancel: () => void;
};

type Props = ConfirmacaoConfig & {
  aberto: boolean;
};

export default function ModalConfirmacao({
  aberto,
  titulo,
  texto,
  rotuloOk,
  perigo = true,
  exigirDigitacao,
  onConfirm,
  onCancel,
}: Props) {
  const [digitacao, setDigitacao] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (!aberto) setDigitacao("");
  }, [aberto]);

  if (!aberto) return null;

  const okHabilitado =
    !exigirDigitacao || digitacao.trim().toLowerCase() === exigirDigitacao.toLowerCase();

  const confirmar = async () => {
    if (!okHabilitado || enviando) return;
    setEnviando(true);
    try {
      await onConfirm();
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="modal-backdrop" role="presentation" onClick={onCancel}>
      <section
        className="modal-detalhe modal-confirmacao"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-confirmacao-titulo"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="modal-detalhe-head">
          <div>
            <h2 id="modal-confirmacao-titulo">{titulo}</h2>
            <p className="meta">Confirme a ação antes de continuar.</p>
          </div>
          <button type="button" className="modal-fechar" aria-label="Fechar" onClick={onCancel}>
            ×
          </button>
        </header>
        <div className="modal-form-body">
          <p>{texto}</p>
          {exigirDigitacao && (
            <label className="field">
              <span className="field-label">
                Digite <strong>{exigirDigitacao}</strong> para confirmar
              </span>
              <input
                className="field-input"
                value={digitacao}
                onChange={(event) => setDigitacao(event.target.value)}
                autoComplete="off"
                spellCheck={false}
                placeholder={exigirDigitacao}
              />
            </label>
          )}
          <div className="modal-form-acoes">
            <button type="button" className="btn-secondary" onClick={onCancel} disabled={enviando}>
              Cancelar
            </button>
            <button
              type="button"
              className={perigo ? "btn-perigo" : "btn-novo"}
              onClick={() => void confirmar()}
              disabled={!okHabilitado || enviando}
            >
              {enviando ? "Aguarde..." : rotuloOk}
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
