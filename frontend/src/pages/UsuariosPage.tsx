import { useEffect, useState } from "react";
import {
  atualizarUsuario,
  criarUsuario,
  excluirUsuario,
  listarUsuarios,
  obterPermissoesPerfis,
  salvarPermissoesPerfis,
} from "../api/leiautes";
import CampoSenha from "../components/CampoSenha";
import ModalConfirmacao, { type ConfirmacaoConfig } from "../components/ModalConfirmacao";
import type { UsuarioPayload, UsuarioResumo } from "../api/types";

type AbaUsuarios = "usuarios" | "perfis";
type Perfil = "operador" | "gestor" | "administrador";

const PERFIS: Perfil[] = ["operador", "gestor", "administrador"];
const USUARIO_VAZIO: UsuarioPayload = {
  nome: "",
  email: "",
  perfil_codigo: "operador",
  cargo: "",
  departamento: "",
  ativo: true,
};

const ROTAS = [
  ["dashboard", "Dashboard", "Visão geral do monitoramento."],
  ["leiautes", "Leiautes", "Cadastro das páginas Bacen monitoradas."],
  ["alteracoes", "Alterações", "Histórico e comparação de versões."],
  ["email-gestor", "E-mail do gestor", "Prévia e envio dos comunicados."],
  ["admin-robo", "Robô", "Execução manual e agenda."],
  ["admin-configuracoes", "Configurações", "Parâmetros operacionais do sistema."],
  ["admin-usuarios", "Usuários e perfis", "Gestão de acessos."],
] as const;

function rotuloPerfil(perfil: string): string {
  if (perfil === "administrador") return "Administrador";
  if (perfil === "gestor") return "Gestor";
  return "Operador";
}

export default function UsuariosPage() {
  const [aba, setAba] = useState<AbaUsuarios>("usuarios");
  const [usuarios, setUsuarios] = useState<UsuarioResumo[]>([]);
  const [permissoes, setPermissoes] = useState<Record<string, string[]>>({});
  const [erro, setErro] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [modalUsuario, setModalUsuario] = useState<UsuarioResumo | "novo" | null>(null);
  const [formUsuario, setFormUsuario] = useState<UsuarioPayload>(USUARIO_VAZIO);
  const [validacaoUsuario, setValidacaoUsuario] = useState<string | null>(null);
  const [confirmacao, setConfirmacao] = useState<ConfirmacaoConfig | null>(null);
  const [definirSenhaApp, setDefinirSenhaApp] = useState(false);
  const [senhaUsuario, setSenhaUsuario] = useState("");

  const carregar = () => {
    setCarregando(true);
    Promise.all([listarUsuarios(), obterPermissoesPerfis()])
      .then(([u, p]) => {
        setUsuarios(u.usuarios);
        setPermissoes(p.permissoes);
      })
      .catch(() => setErro("API indisponível."))
      .finally(() => setCarregando(false));
  };

  useEffect(() => {
    carregar();
  }, []);

  const alternar = (perfil: Perfil, rota: string) => {
    if (perfil === "administrador") return;
    setPermissoes((atual) => {
      const rotas = new Set(atual[perfil] ?? []);
      if (rotas.has(rota)) rotas.delete(rota);
      else rotas.add(rota);
      return { ...atual, [perfil]: [...rotas] };
    });
  };

  const salvar = async () => {
    setSalvando(true);
    setErro(null);
    setMsg(null);
    try {
      const resp = await salvarPermissoesPerfis(permissoes);
      setPermissoes(resp.permissoes);
      setMsg("Permissões salvas.");
    } catch {
      setErro("Não foi possível salvar permissões.");
    } finally {
      setSalvando(false);
    }
  };

  const abrirNovoUsuario = () => {
    setModalUsuario("novo");
    setFormUsuario(USUARIO_VAZIO);
    setDefinirSenhaApp(false);
    setSenhaUsuario("");
    setValidacaoUsuario(null);
    setErro(null);
    setMsg(null);
  };

  const abrirEditarUsuario = (usuario: UsuarioResumo) => {
    setModalUsuario(usuario);
    setFormUsuario({
      nome: usuario.nome,
      email: usuario.email,
      perfil_codigo: usuario.perfil_codigo as Perfil,
      cargo: usuario.cargo ?? "",
      departamento: usuario.departamento ?? "",
      ativo: usuario.ativo,
    });
    setDefinirSenhaApp(false);
    setSenhaUsuario("");
    setValidacaoUsuario(null);
    setErro(null);
    setMsg(null);
  };

  const validarUsuario = (): string | null => {
    if (formUsuario.nome.trim().length < 2) return "Informe o nome do usuário.";
    if (!formUsuario.email.includes("@")) return "Informe um e-mail válido.";
    if (!PERFIS.includes(formUsuario.perfil_codigo)) return "Selecione um perfil válido.";
    if (definirSenhaApp && senhaUsuario.trim().length === 0) {
      return "Marcou senha neste app. Informe a senha ou desmarque a opção.";
    }
    return null;
  };

  const salvarUsuario = async () => {
    const problema = validarUsuario();
    if (problema) {
      setValidacaoUsuario(problema);
      return;
    }
    setSalvando(true);
    setErro(null);
    setMsg(null);
    setValidacaoUsuario(null);
    try {
      if (modalUsuario === "novo") {
        await criarUsuario({
          ...formUsuario,
          ...(definirSenhaApp ? { senha_inicial: senhaUsuario.trim() } : {}),
        });
        setMsg(
          definirSenhaApp
            ? "Usuário criado com senha local."
            : "Usuário criado para acesso pelo portal Finaud.",
        );
      } else if (modalUsuario) {
        await atualizarUsuario(modalUsuario.id, {
          ...formUsuario,
          ...(definirSenhaApp ? { nova_senha: senhaUsuario.trim() } : {}),
        });
        setMsg("Usuário atualizado.");
      }
      setModalUsuario(null);
      carregar();
    } catch {
      setErro("Não foi possível salvar o usuário. Verifique se o e-mail já existe.");
    } finally {
      setSalvando(false);
    }
  };

  const alternarUsuarioAtivo = (usuario: UsuarioResumo) => {
    const inativar = usuario.ativo;
    setConfirmacao({
      titulo: inativar ? "Inativar usuário" : "Ativar usuário",
      texto: inativar
        ? `Inativar "${usuario.nome}" (${usuario.email})? O usuário deixará de acessar até ser reativado.`
        : `Ativar "${usuario.nome}" (${usuario.email}) novamente?`,
      rotuloOk: inativar ? "Inativar" : "Ativar",
      perigo: inativar,
      onCancel: () => setConfirmacao(null),
      onConfirm: async () => {
        await atualizarUsuario(usuario.id, {
          nome: usuario.nome,
          email: usuario.email,
          perfil_codigo: usuario.perfil_codigo as Perfil,
          cargo: usuario.cargo,
          departamento: usuario.departamento,
          ativo: !usuario.ativo,
        });
        setConfirmacao(null);
        setMsg(inativar ? "Usuário inativado." : "Usuário ativado.");
        carregar();
      },
    });
  };

  const excluir = (usuario: UsuarioResumo) => {
    setConfirmacao({
      titulo: "Excluir usuário",
      texto: `Excluir permanentemente "${usuario.nome}" (${usuario.email})? Esta ação não pode ser desfeita.`,
      rotuloOk: "Excluir",
      exigirDigitacao: "excluir",
      onCancel: () => setConfirmacao(null),
      onConfirm: async () => {
        try {
          await excluirUsuario(usuario.id);
          setConfirmacao(null);
          setMsg("Usuário excluído.");
          carregar();
        } catch (e) {
          setConfirmacao(null);
          setErro(e instanceof Error ? e.message : "Não foi possível excluir o usuário.");
        }
      },
    });
  };

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">Usuários e perfis</h1>
          <p className="page-sub">Quem acessa o sistema e o que cada perfil pode ver.</p>
        </div>
        {aba === "usuarios" ? (
          <button type="button" className="btn-novo" onClick={abrirNovoUsuario}>
            + Novo usuário
          </button>
        ) : (
          <button
            type="button"
            className="btn-novo"
            disabled={salvando}
            onClick={() => void salvar()}
          >
            {salvando ? "Salvando..." : "Salvar permissões"}
          </button>
        )}
      </div>

      <p className="admin-ajuda">
        A estrutura segue o padrão do normativos_ia: o perfil controla quais telas
        aparecem no menu lateral. Sem senha local, o usuário fica liberado para entrar
        pelo portal Finaud; com senha local, acessa este app diretamente.
      </p>

      <div className="admin-tabs config-abas" role="tablist">
        <button
          type="button"
          className={aba === "usuarios" ? "ativo" : ""}
          onClick={() => setAba("usuarios")}
        >
          Usuários
        </button>
        <button
          type="button"
          className={aba === "perfis" ? "ativo" : ""}
          onClick={() => setAba("perfis")}
        >
          Perfis e permissões
        </button>
      </div>

      {erro && <p className="erro">{erro}</p>}
      {msg && <p className="login-sucesso">{msg}</p>}
      {carregando && <p className="meta">Carregando...</p>}

      {aba === "usuarios" ? (
        <div className="tabela-wrap">
          <table className="tabela">
            <thead>
              <tr>
                <th>Usuário</th>
                <th>Perfil</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {usuarios.length === 0 ? (
                <tr>
                  <td colSpan={4} className="meta">
                    Nenhum usuário cadastrado. Use o botão Novo usuário para iniciar.
                  </td>
                </tr>
              ) : (
                usuarios.map((usuario) => (
                  <tr key={usuario.id}>
                    <td>
                      <strong>{usuario.nome}</strong>
                      <div className="meta">{usuario.email}</div>
                    </td>
                    <td>
                      <span className={`badge-perfil badge-perfil-${usuario.perfil_codigo}`}>
                        {rotuloPerfil(usuario.perfil_codigo)}
                      </span>
                    </td>
                    <td className={usuario.ativo ? "status-ok" : "status-erro"}>
                      {usuario.ativo ? "Ativo" : "Inativo"}
                    </td>
                    <td>
                      <div className="acoes-linha">
                        <button
                          type="button"
                          className="btn-secondary"
                          onClick={() => abrirEditarUsuario(usuario)}
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          className="btn-secondary"
                          onClick={() => alternarUsuarioAtivo(usuario)}
                        >
                          {usuario.ativo ? "Inativar" : "Ativar"}
                        </button>
                        <button
                          type="button"
                          className="btn-perigo"
                          onClick={() => excluir(usuario)}
                        >
                          Excluir
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="config-painel-aba">
          <div className="tabela-wrap">
            <table className="tabela tabela-compacta">
              <thead>
                <tr>
                  <th>Tela</th>
                  {PERFIS.map((perfil) => (
                    <th key={perfil}>{rotuloPerfil(perfil)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ROTAS.map(([rota, label, motivo]) => (
                  <tr key={rota}>
                    <td>
                      <strong>{label}</strong>
                      <div className="meta">{motivo}</div>
                    </td>
                    {PERFIS.map((perfil) => {
                      const tem = perfil === "administrador" || permissoes[perfil]?.includes(rota);
                      return (
                        <td key={perfil}>
                          <button
                            type="button"
                            className={`permissao-toggle ${tem ? "permissao-toggle-sim" : ""}`}
                            disabled={perfil === "administrador"}
                            onClick={() => alternar(perfil, rota)}
                          >
                            {tem ? "Sim" : "Não"}
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {modalUsuario && (
        <div className="modal-backdrop" onClick={() => setModalUsuario(null)}>
          <section
            className="modal-detalhe modal-form"
            role="dialog"
            aria-modal="true"
            onClick={(event) => event.stopPropagation()}
          >
            <header className="modal-detalhe-head">
              <div>
                <h2>{modalUsuario === "novo" ? "Novo usuário" : "Editar usuário"}</h2>
                <p className="meta">Defina os dados de acesso e o perfil do usuário.</p>
              </div>
              <button
                type="button"
                className="modal-fechar"
                aria-label="Fechar"
                onClick={() => setModalUsuario(null)}
              >
                ×
              </button>
            </header>
            <div className="modal-form-body">
              {validacaoUsuario && <p className="erro">{validacaoUsuario}</p>}
              <label className="field">
                <span className="field-label">Nome</span>
                <input
                  className="field-input"
                  value={formUsuario.nome}
                  onChange={(e) =>
                    setFormUsuario({ ...formUsuario, nome: e.target.value })
                  }
                />
              </label>
              <label className="field">
                <span className="field-label">E-mail</span>
                <input
                  className="field-input"
                  value={formUsuario.email}
                  onChange={(e) =>
                    setFormUsuario({ ...formUsuario, email: e.target.value })
                  }
                />
              </label>
              <div className="config-dupla">
                <label className="field">
                  <span className="field-label">Perfil</span>
                  <select
                    className="field-input"
                    value={formUsuario.perfil_codigo}
                    onChange={(e) =>
                      setFormUsuario({
                        ...formUsuario,
                        perfil_codigo: e.target.value as Perfil,
                      })
                    }
                  >
                    {PERFIS.map((perfil) => (
                      <option key={perfil} value={perfil}>
                        {rotuloPerfil(perfil)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span className="field-label">Cargo</span>
                  <input
                    className="field-input"
                    value={formUsuario.cargo ?? ""}
                    onChange={(e) =>
                      setFormUsuario({ ...formUsuario, cargo: e.target.value })
                    }
                  />
                </label>
              </div>
              <label className="field">
                <span className="field-label">Departamento</span>
                <input
                  className="field-input"
                  value={formUsuario.departamento ?? ""}
                  onChange={(e) =>
                    setFormUsuario({ ...formUsuario, departamento: e.target.value })
                  }
                />
              </label>
              <label className="field-check">
                <input
                  type="checkbox"
                  checked={definirSenhaApp}
                  onChange={(e) => {
                    setDefinirSenhaApp(e.target.checked);
                    if (!e.target.checked) setSenhaUsuario("");
                  }}
                />
                Definir senha neste app
              </label>
              <p className="meta">
                Normalmente deixe desmarcado para usar o portal Finaud. Marque apenas para
                senha local ou reset temporário.
              </p>
              {definirSenhaApp && (
                <CampoSenha
                  id="usuario-senha"
                  label={modalUsuario === "novo" ? "Senha inicial" : "Nova senha"}
                  autoComplete="new-password"
                  value={senhaUsuario}
                  onChange={setSenhaUsuario}
                />
              )}
              <label className="admin-dia-chip">
                <input
                  type="checkbox"
                  checked={formUsuario.ativo}
                  onChange={(e) =>
                    setFormUsuario({ ...formUsuario, ativo: e.target.checked })
                  }
                />
                Usuário ativo
              </label>
              <div className="modal-form-acoes">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setModalUsuario(null)}
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  className="btn-novo"
                  disabled={salvando}
                  onClick={() => void salvarUsuario()}
                >
                  {salvando ? "Salvando..." : "Salvar usuário"}
                </button>
              </div>
            </div>
          </section>
        </div>
      )}
      {confirmacao && <ModalConfirmacao aberto {...confirmacao} />}
    </div>
  );
}
