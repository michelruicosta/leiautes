import { type FormEvent, useState } from "react";
import { recuperarSenhaAuth } from "../api/auth";
import { ApiError } from "../api/client";
import CampoSenha from "../components/CampoSenha";
import { useAuth } from "../context/AuthContext";

const URL_PORTAL_APPS =
  (import.meta.env.VITE_PORTAL_URL as string | undefined)?.replace(/\/$/, "") ||
  "https://finaudapps.com.br";

type Modo = "login" | "recuperar";

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
  const [modo, setModo] = useState<Modo>("login");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const onLogin = async (e: FormEvent) => {
    e.preventDefault();
    setErro(null);
    setSucesso(null);
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

  const onRecuperar = async (e: FormEvent) => {
    e.preventDefault();
    setErro(null);
    setSucesso(null);
    setEnviando(true);
    try {
      const resposta = await recuperarSenhaAuth(email.trim());
      setSucesso(resposta.mensagem);
    } catch (err) {
      setErro(
        err instanceof ApiError
          ? err.message
          : "Não foi possível enviar o pedido. Tente novamente.",
      );
    } finally {
      setEnviando(false);
    }
  };

  if (modo === "recuperar") {
    return (
      <div className="login-shell login-shell-finaud">
        <form
          className="login-card login-card-finaud"
          onSubmit={(e) => void onRecuperar(e)}
        >
          <CabecalhoLoginLeiautes />
          <h2 className="login-titulo login-titulo-finaud">Recuperar acesso</h2>
          <p className="login-subtitulo">
            Informe seu e-mail corporativo. Se a conta estiver ativa, enviamos
            uma senha temporária.
          </p>

          <div className="field">
            <label className="field-label" htmlFor="recuperar-email">
              E-mail
            </label>
            <input
              id="recuperar-email"
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

          {erro && <p className="login-erro">{erro}</p>}
          {sucesso && <p className="login-sucesso">{sucesso}</p>}

          <button
            type="submit"
            className="btn-primary login-submit"
            disabled={enviando || !!sucesso}
          >
            {enviando
              ? "Enviando…"
              : sucesso
                ? "E-mail solicitado"
                : "Enviar senha temporária"}
          </button>

          <p className="login-rodape">
            <button
              type="button"
              className="btn-link"
              onClick={() => {
                setModo("login");
                setErro(null);
                setSucesso(null);
              }}
            >
              Voltar ao login
            </button>
          </p>
          <a className="login-portal-link" href={URL_PORTAL_APPS}>
            Portal de apps
          </a>
        </form>
      </div>
    );
  }

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

        <p className="login-rodape">
          <button
            type="button"
            className="btn-link"
            onClick={() => {
              setModo("recuperar");
              setErro(null);
              setSucesso(null);
            }}
          >
            Esqueceu a senha?
          </button>
        </p>
        <a className="login-portal-link" href={URL_PORTAL_APPS}>
          Portal de apps
        </a>
      </form>
    </div>
  );
}
