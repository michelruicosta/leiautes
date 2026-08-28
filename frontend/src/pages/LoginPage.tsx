import { type FormEvent, useState } from "react";
import { ApiError } from "../api/client";
import CampoSenha from "../components/CampoSenha";
import { useAuth, urlPortalApps } from "../context/AuthContext";

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

export default function LoginPage() {
  const { entrar } = useAuth();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const onLogin = async (e: FormEvent) => {
    e.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      await entrar(email.trim(), senha);
    } catch (err) {
      setErro(
        err instanceof ApiError
          ? err.message
          : "Não foi possível entrar. Tente novamente.",
      );
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="login-shell login-shell-finaud">
      <form
        className="login-card login-card-finaud"
        onSubmit={(e) => void onLogin(e)}
      >
        <CabecalhoLoginLeiautes />

        <div className="field">
          <label className="field-label" htmlFor="login-email">
            E-mail
          </label>
          <input
            id="login-email"
            className="field-input"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            onInvalid={(e) => {
              e.currentTarget.setCustomValidity("Informe seu e-mail.");
            }}
            onInput={(e) => e.currentTarget.setCustomValidity("")}
          />
        </div>

        <CampoSenha
          id="login-senha"
          label="Senha"
          autoComplete="current-password"
          value={senha}
          onChange={setSenha}
          required
        />

        {erro && <p className="login-erro">{erro}</p>}

        <button
          type="submit"
          className="btn-primary login-submit"
          disabled={enviando}
        >
          {enviando ? "Entrando…" : "Entrar"}
        </button>

        <a className="login-portal-link" href={urlPortalApps()}>
          Portal de apps
        </a>
      </form>
    </div>
  );
}
