import { type FormEvent, useMemo, useState } from "react";
import { alterarSenhaAuth } from "../api/auth";
import { ApiError } from "../api/client";
import CampoSenha from "../components/CampoSenha";
import RequisitosSenha, { senhaAtendePolitica } from "../components/RequisitosSenha";

type Props = {
  onVoltarPerfil: () => void;
};

export default function AlterarSenhaPage({ onVoltarPerfil }: Props) {
  const [senhaAtual, setSenhaAtual] = useState("");
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const senhasCoincidem = confirmar.length === 0 || novaSenha === confirmar;
  const podeSalvar = useMemo(() => {
    return (
      senhaAtual.trim().length > 0 &&
      senhaAtendePolitica(novaSenha) &&
      novaSenha === confirmar &&
      novaSenha !== senhaAtual &&
      !enviando &&
      !sucesso
    );
  }, [senhaAtual, novaSenha, confirmar, enviando, sucesso]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setErro(null);
    setSucesso(null);
    if (!podeSalvar) return;
    setEnviando(true);
    try {
      const res = await alterarSenhaAuth(senhaAtual, novaSenha, confirmar);
      setSucesso(res.mensagem);
      setSenhaAtual("");
      setNovaSenha("");
      setConfirmar("");
    } catch (err) {
      setErro(
        err instanceof ApiError
          ? err.message
          : "Não foi possível alterar a senha.",
      );
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="perfil-shell">
      <form
        className="perfil-card"
        onSubmit={(e) => void onSubmit(e)}
        noValidate
      >
        <h1 className="login-titulo">Alterar senha</h1>
        <p className="login-subtitulo">
          Crie uma senha forte para proteger sua conta.
        </p>

        <CampoSenha
          id="senha-atual"
          label="Senha atual"
          autoComplete="current-password"
          value={senhaAtual}
          onChange={setSenhaAtual}
          required
        />
        <CampoSenha
          id="nova-senha"
          label="Nova senha"
          autoComplete="new-password"
          value={novaSenha}
          onChange={setNovaSenha}
          required
          aria-describedby="requisitos-senha"
        />
        <RequisitosSenha senha={novaSenha} />
        <CampoSenha
          id="confirmar-senha"
          label="Confirmar nova senha"
          autoComplete="new-password"
          value={confirmar}
          onChange={setConfirmar}
          required
        />
        {!senhasCoincidem && (
          <p className="perfil-aviso">As senhas não coincidem.</p>
        )}

        {erro && <p className="login-erro">{erro}</p>}
        {sucesso && <p className="login-sucesso">{sucesso}</p>}

        <div className="perfil-acoes">
          <button
            type="button"
            className="btn-secondary"
            onClick={onVoltarPerfil}
          >
            Voltar ao perfil
          </button>
          <button
            type="submit"
            className="btn-primary"
            disabled={!podeSalvar}
          >
            {enviando ? "Salvando…" : "Atualizar senha"}
          </button>
        </div>
      </form>
    </div>
  );
}
