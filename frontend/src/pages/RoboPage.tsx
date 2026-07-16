import { useEffect, useState } from "react";
import { obterStatusRobo } from "../api/leiautes";
import type { RoboStatusResponse } from "../api/types";

export default function RoboPage() {
  const [status, setStatus] = useState<RoboStatusResponse | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    obterStatusRobo().then(setStatus).catch(() => setErro("API indisponível."));
  }, []);

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">Robô</h1>
          <p className="page-sub">Execução manual, status e histórico operacional.</p>
        </div>
        <button type="button" className="btn-novo">
          Executar agora
        </button>
      </div>

      {erro && <p className="erro">{erro}</p>}

      <article className="card">
        <h2>Status do motor</h2>
        <p className="meta">{status?.script_motor ?? "—"}</p>
        <p className={status?.script_existe ? "status-ok" : "status-erro"}>
          {status?.script_existe ? "Script encontrado" : "Script não encontrado"}
        </p>
      </article>
    </div>
  );
}
