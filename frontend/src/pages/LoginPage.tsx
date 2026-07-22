import { type FormEvent, useState } from "react";
import { recuperarSenhaAuth } from "../api/auth";
import { ApiError } from "../api/client";
import CampoSenha from "../components/CampoSenha";
import MarcaOrganizacao from "../components/MarcaOrganizacao";
import { useAuth } from "../context/AuthContext";

type Modo = "login" | "recuperar";

export default function LoginPage() {
  const { entrar } = useAuth();
  const [modo, setModo] = useState<Modo>("login");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const cabecalho = (
    <MarcaOrganizacao
      nome="FINAUD TEC"
      subtitulo="Leiautes Bacen · Monitoramento"
    />
  );

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
      <div className="login-shell login-shell-marca">
        <form
          className="login-card login-card-marca"
          onSubmit={(e) => void onRecuperar(e)}
        >
          {cabecalho}
          <h2 className="login-titulo-secundario">Recuperar acesso</h2>
          <p className="login-subtitulo-recuperar">
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
              ← Voltar ao login
            </button>
          </p>
        </form>
      </div>
    );
  }

  return (
    <div className="login-shell login-shell-marca">
      <form className="login-card login-card-marca" onSubmit={(e) => void onLogin(e)}>
        {cabecalho}

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

        <button type="submit" className="btn-primary login-submit" disabled={enviando}>
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
      </form>
    </div>
  );
}
