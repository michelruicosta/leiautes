import { type FormEvent, useState } from "react";
import { loginAuth, recuperarSenhaAuth, type UsuarioAuth } from "../api/auth";
import { ApiError } from "../api/client";
import CampoSenha from "../components/CampoSenha";

type Props = {
  onEntrar: (usuario: UsuarioAuth) => void;
};

type Modo = "login" | "recuperar";

export default function LoginPage({ onEntrar }: Props) {
  const [modo, setModo] = useState<Modo>("login");
  const [email, setEmail] = useState("gestor@finaud.com.br");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const entrar = async (event: FormEvent) => {
    event.preventDefault();
    setErro(null);
    setMensagem(null);
    setEnviando(true);
    try {
      const resp = await loginAuth(email.trim(), senha);
      onEntrar(resp.usuario);
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Não foi possível entrar.");
    } finally {
      setEnviando(false);
    }
  };

  const recuperar = async (event: FormEvent) => {
    event.preventDefault();
    setErro(null);
    setMensagem(null);
    setEnviando(true);
    try {
      const resp = await recuperarSenhaAuth(email.trim());
      setMensagem(resp.mensagem);
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Não foi possível solicitar recuperação.");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="login-shell login-shell-marca">
      <form
        className="login-card login-card-marca"
        onSubmit={(e) => void (modo === "login" ? entrar(e) : recuperar(e))}
      >
        <div className="marca-org">
          <div className="marca-org-logo-placeholder">FT</div>
          <div className="marca-org-textos">
            <strong className="marca-org-nome">FINAUD TEC</strong>
            <span className="marca-org-sub">Leiautes Bacen · Monitoramento</span>
          </div>
        </div>

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

        {modo === "login" ? (
          <CampoSenha
            id="login-senha"
            label="Senha"
            autoComplete="current-password"
            value={senha}
            onChange={setSenha}
            required
          />
        ) : (
          <p className="meta">
            Informe o e-mail. Se a conta estiver ativa, a recuperação será registrada.
          </p>
        )}

        {erro && <p className="erro">{erro}</p>}
        {mensagem && <p className="login-sucesso">{mensagem}</p>}
        <button type="submit" className="btn-primary login-submit">
          {enviando
            ? "Aguarde..."
            : modo === "login"
              ? "Entrar"
              : "Solicitar recuperação"}
        </button>

        <p className="login-rodape">
          <button
            type="button"
            className="btn-link"
            onClick={() => {
              setModo(modo === "login" ? "recuperar" : "login");
              setErro(null);
              setMensagem(null);
            }}
          >
            {modo === "login" ? "Esqueceu a senha?" : "Voltar ao login"}
          </button>
        </p>
      </form>
    </div>
  );
}
