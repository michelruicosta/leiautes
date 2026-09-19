import { urlPortalApps } from "../context/AuthContext";

function CabecalhoLoginLeiautes() {
  return (
    <div className="login-finaud-topo">
      <div className="login-finaud-ico" aria-hidden>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
          <path d="M7 3h7l5 5v13H7z" />
          <path d="M14 3v5h5" />
          <path d="M10 12h6M10 16h6" />
        </svg>
      </div>
      <p className="login-finaud-kicker">Grupo Finaud</p>
      <h1 className="login-finaud-titulo">Leiautes Bacen</h1>
      <p className="login-finaud-sub">Monitoramento</p>
    </div>
  );
}

/** Sem login local: o acesso vem só da sessão do portal Finaud (SSO). */
export default function LoginPage() {
  return (
    <div className="login-shell login-shell-finaud">
      <div className="login-card login-card-finaud">
        <CabecalhoLoginLeiautes />

        <p className="login-finaud-sub login-finaud-aviso">
          Sua sessão no portal Finaud não foi encontrada ou expirou. Entre pelo
          portal e abra o Leiautes Bacen de lá.
        </p>

        <a className="btn-primary login-submit" href={urlPortalApps()}>
          Entrar pelo portal
        </a>
      </div>
    </div>
  );
}
