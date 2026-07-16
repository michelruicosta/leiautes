import { useEffect, useState } from "react";
import { listarLeiautes } from "../api/leiautes";
import type { LeiauteResumo } from "../api/types";

export default function LeiautesPage() {
  const [itens, setItens] = useState<LeiauteResumo[]>([]);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    listarLeiautes()
      .then((resp) => setItens(resp.leiautes))
      .catch(() => setErro("API indisponível."));
  }, []);

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">Leiautes</h1>
          <p className="page-sub">Páginas Bacen e tipos de arquivo monitorados.</p>
        </div>
        <button type="button" className="btn-novo">
          + Novo leiaute
        </button>
      </div>

      {erro && <p className="erro">{erro}</p>}

      <div className="tabela-wrap">
        <table className="tabela">
          <thead>
            <tr>
              <th>Código</th>
              <th>Nome</th>
              <th>Categoria</th>
              <th>Tipos</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {itens.map((item) => (
              <tr key={item.id}>
                <td>
                  <strong>{item.codigo}</strong>
                </td>
                <td>{item.nome}</td>
                <td>{item.categoria}</td>
                <td>
                  <div className="tags-inline">
                    {item.tipos_arquivo.map((tipo) => (
                      <span key={tipo} className="tag">
                        {tipo.toUpperCase()}
                      </span>
                    ))}
                  </div>
                </td>
                <td className={item.ativo ? "status-ok" : "status-erro"}>
                  {item.ativo ? "Ativo" : "Inativo"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
