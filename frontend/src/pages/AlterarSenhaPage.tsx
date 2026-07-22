import { type FormEvent, useMemo, useState } from "react";
import { alterarSenhaAuth } from "../api/auth";
import { ApiError } from "../api/client";
import CampoSenha from "../components/CampoSenha";
import RequisitosSenha, { senhaAtendePolitica } from "../components/RequisitosSenha";

type Props = {
  onVoltar: () => void;
};

export default function AlterarSenhaPage({ onVoltar }: Props) {
  const [senhaAtual, setSenhaAtual] = useState("");
  const [novaSenha, setNovaSenha] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const podeSalvar = useMemo(() => {
    return (
      senhaAtual.trim().length > 0 &&
      senhaAtendePolitica(novaSenha) &&
      novaSenha === confirmar &&
      novaSenha !== senhaAtual &&
      !enviando
    );
  }, [senhaAtual, novaSenha, confirmar, enviando]);

  const feedbackConfirmar = useMemo(() => {
    if (!confirmar) return null;
    if (novaSenha === confirmar) return { ok: true, texto: "As senhas coincidem." };
    return { ok: false, texto: "As senhas não coincidem." };
  }, [novaSenha, confirmar]);

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
    <div className="admin-page">
      <button type="button" className="voltar" onClick={onVoltar}>
        ← Voltar
      </button>
      <h1 className="page-title">Alterar senha</h1>
      <p className="page-sub">Atualize sua senha de acesso ao sistema</p>
      <form
        className="perfil-card alterar-senha-card"
        onSubmit={(e) => void onSubmit(e)}
        noValidate
      >
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
        {feedbackConfirmar && (
          <p className={feedbackConfirmar.ok ? "senha-feedback ok" : "senha-feedback erro"}>
            {feedbackConfirmar.texto}
          </p>
        )}
        {erro && <p className="login-erro">{erro}</p>}
        {sucesso && <p className="login-sucesso">{sucesso}</p>}
        <button type="submit" className="btn-primary login-submit" disabled={!podeSalvar}>
          {enviando ? "Salvando…" : "Salvar"}
        </button>
      </form>
    </div>
  );
}
