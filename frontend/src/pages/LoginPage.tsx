type Props = {
  onEntrar: () => void;
};

export default function LoginPage({ onEntrar }: Props) {
  return (
    <div className="login-shell login-shell-marca">
      <form
        className="login-card login-card-marca"
        onSubmit={(e) => {
          e.preventDefault();
          onEntrar();
        }}
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
            defaultValue="gestor@finaud.com.br"
            required
          />
        </div>

        <div className="field">
          <label className="field-label" htmlFor="login-senha">
            Senha
          </label>
          <input
            id="login-senha"
            className="field-input"
            type="password"
            autoComplete="current-password"
            defaultValue="senha-temporaria"
            required
          />
        </div>

        <button type="submit" className="btn-primary login-submit">
          Entrar
        </button>

        <p className="login-rodape">
          <button type="button" className="btn-link">
            Esqueceu a senha?
          </button>
        </p>
      </form>
    </div>
  );
}
