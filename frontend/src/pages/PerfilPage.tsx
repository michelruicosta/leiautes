import { useAuth } from "../context/AuthContext";

type Props = {
  onAlterarSenha: () => void;
  onVoltarHome: () => void;
  /** Nome da organização exibido (Leiautes não tem multi-org no auth). */
  organizacaoNome?: string;
};

function rotuloPerfil(codigo: string): string {
  if (codigo === "administrador") return "Administrador";
  if (codigo === "gestor") return "Gestor";
  if (codigo === "operador") return "Operador";
  return codigo;
}

function iniciais(nome: string): string {
  const partes = nome.trim().split(/\s+/).filter(Boolean);
  if (partes.length === 0) return "?";
  if (partes.length === 1) return partes[0].slice(0, 2).toUpperCase();
  return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase();
}

export default function PerfilPage({
  onAlterarSenha,
  onVoltarHome,
  organizacaoNome = "FINAUD TEC",
}: Props) {
  const { usuario } = useAuth();

  if (!usuario) return null;

  return (
    <div className="perfil-shell">
      <div className="perfil-card perfil-card-largo">
        <div className="perfil-topo">
          <div className="perfil-avatar" aria-hidden>
            {iniciais(usuario.nome)}
          </div>
          <span className="perfil-badge">{rotuloPerfil(usuario.perfil_codigo)}</span>
        </div>

        <h1 className="login-titulo">{usuario.nome}</h1>
        <p className="login-subtitulo">{usuario.email}</p>

        <dl className="perfil-lista">
          <div>
            <dt>Organização</dt>
            <dd>{organizacaoNome}</dd>
          </div>
          <div>
            <dt>Perfil no sistema</dt>
            <dd>{rotuloPerfil(usuario.perfil_codigo)}</dd>
          </div>
          {usuario.cargo && (
            <div>
              <dt>Cargo</dt>
              <dd>{usuario.cargo}</dd>
            </div>
          )}
          {usuario.departamento && (
            <div>
              <dt>Departamento</dt>
              <dd>{usuario.departamento}</dd>
            </div>
          )}
        </dl>

        <div className="perfil-acoes">
          <button type="button" className="btn-secondary" onClick={onVoltarHome}>
            Voltar
          </button>
          <button type="button" className="btn-primary" onClick={onAlterarSenha}>
            Alterar senha
          </button>
        </div>
      </div>
    </div>
  );
}
