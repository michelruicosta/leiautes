import { useEffect, useMemo, useState } from "react";
import {
  listarUsuarios,
  obterPermissoesPerfis,
  salvarPermissoesPerfis,
} from "../api/leiautes";
import type { UsuarioResumo } from "../api/types";

type AbaUsuarios = "usuarios" | "perfis";
type Perfil = "operador" | "gestor" | "administrador";

const PERFIS: Perfil[] = ["operador", "gestor", "administrador"];

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

  useEffect(() => {
    setCarregando(true);
    Promise.all([listarUsuarios(), obterPermissoesPerfis()])
      .then(([u, p]) => {
        setUsuarios(u.usuarios);
        setPermissoes(p.permissoes);
      })
      .catch(() => setErro("API indisponível."))
      .finally(() => setCarregando(false));
  }, []);

  const usuariosExibidos = useMemo(() => {
    if (usuarios.length > 0) return usuarios;
    return [
      {
        id: 1,
        nome: "Bruna",
        email: "bruna@finaud.com.br",
        perfil_codigo: "administrador",
        ativo: true,
      },
      {
        id: 2,
        nome: "Gestor Finaud",
        email: "gestor@finaud.com.br",
        perfil_codigo: "gestor",
        ativo: true,
      },
    ];
  }, [usuarios]);

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

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">Usuários e perfis</h1>
          <p className="page-sub">Quem acessa o sistema e o que cada perfil pode ver.</p>
        </div>
        {aba === "usuarios" ? (
          <button type="button" className="btn-novo">
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
        aparecem no menu lateral.
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
              {usuariosExibidos.map((usuario) => (
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
                    <button type="button" className="btn-secondary">
                      Editar
                    </button>
                  </td>
                </tr>
              ))}
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
    </div>
  );
}
