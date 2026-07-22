type Props = {
  titulo: string;
  subtitulo: string;
};

export default function PlaceholderPage({ titulo, subtitulo }: Props) {
  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">{titulo}</h1>
          <p className="page-sub">{subtitulo}</p>
        </div>
      </div>
      <p className="admin-ajuda">
        Tela prevista no protótipo e no checklist. A implementação detalhada entra nas
        próximas etapas, mantendo o mesmo padrão visual do projeto normativos_ia.
      </p>
    </div>
  );
}
