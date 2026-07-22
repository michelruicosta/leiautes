type Props = {
  nome: string;
  logoUrl?: string | null;
  subtitulo?: string;
  compacto?: boolean;
};

export function urlLogoApi(
  caminho: string | null | undefined,
  versao?: number | null,
): string | null {
  if (!caminho) return null;
  const base = import.meta.env.VITE_API_BASE ?? "/api";
  const url = `${base}${caminho}`;
  if (versao == null) return url;
  return `${url}?v=${versao}`;
}

export default function MarcaOrganizacao({
  nome,
  logoUrl,
  subtitulo,
  compacto = false,
}: Props) {
  return (
    <div className={`marca-org${compacto ? " marca-org-compacto" : ""}`}>
      {logoUrl ? (
        <div className="marca-org-logo-quadro">
          <img className="marca-org-logo" src={logoUrl} alt={`Logo ${nome}`} />
        </div>
      ) : (
        <div className="marca-org-logo-placeholder" aria-hidden>
          {nome.slice(0, 1).toUpperCase()}
        </div>
      )}
      <div className="marca-org-textos">
        <strong className="marca-org-nome">{nome}</strong>
        {subtitulo && <span className="marca-org-sub">{subtitulo}</span>}
      </div>
    </div>
  );
}
