import { useEffect, useRef, useState, type ReactNode } from "react";
import { useAuth } from "../context/AuthContext";

export type RotaPainel =
  | "dashboard"
  | "leiautes"
  | "alteracoes"
  | "robo"
  | "configuracoes"
  | "usuarios"
  | "auditoria"
  | "perfil"
  | "alterar-senha";

/** Código da matriz de permissões → rota do painel. */
const ROTA_PARA_PERMISSAO: Record<
  Exclude<RotaPainel, "alterar-senha" | "perfil">,
  string
> = {
  dashboard: "dashboard",
  leiautes: "leiautes",
  alteracoes: "alteracoes",
  robo: "admin-robo",
  configuracoes: "admin-configuracoes",
  usuarios: "admin-usuarios",
  auditoria: "admin-auditoria",
};

type Props = {
  rota: RotaPainel;
  onNavegar: (rota: RotaPainel) => void;
  children: ReactNode;
};

const URL_PORTAL_APPS = "https://finaudapps.com.br";

function MenuUsuario({
  onPerfil,
  onSair,
}: {
  onPerfil: () => void;
  onSair: () => void;
}) {
  const { usuario } = useAuth();
  const [menuAberto, setMenuAberto] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!menuAberto) return;
    const fechar = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuAberto(false);
      }
    };
    document.addEventListener("mousedown", fechar);
    return () => document.removeEventListener("mousedown", fechar);
  }, [menuAberto]);

  if (!usuario) return null;

  const escolher = (acao: () => void) => {
    setMenuAberto(false);
    acao();
  };

  return (
    <div className="app-menu" ref={menuRef}>
      <button
        type="button"
        className="app-menu-trigger"
        aria-haspopup="menu"
        aria-expanded={menuAberto}
        onClick={() => setMenuAberto((v) => !v)}
      >
        {usuario.nome}
        <span className="app-menu-chevron" aria-hidden>
          ▾
        </span>
      </button>
      {menuAberto && (
        <ul className="app-menu-list" role="menu">
          <li role="none">
            <a
              role="menuitem"
              className="app-menu-item app-menu-link"
              href={URL_PORTAL_APPS}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setMenuAberto(false)}
            >
              Portal de apps ↗
            </a>
          </li>
          <li role="none">
            <button
              type="button"
              role="menuitem"
              className="app-menu-item"
              onClick={() => escolher(onPerfil)}
            >
              Perfil
            </button>
          </li>
          <li role="none">
            <button
              type="button"
              role="menuitem"
              className="app-menu-item app-menu-item-perigo"
              onClick={() => escolher(onSair)}
            >
              Sair
            </button>
          </li>
        </ul>
      )}
    </div>
  );
}

export function podeAcessarRota(
  rota: RotaPainel,
  rotasPermitidas: string[] | undefined,
): boolean {
  if (rota === "alterar-senha" || rota === "perfil") return true;
  const codigo = ROTA_PARA_PERMISSAO[rota];
  return (rotasPermitidas ?? []).includes(codigo);
}

export default function AppShell({ rota, onNavegar, children }: Props) {
  const { usuario, sair } = useAuth();
  const permitidas = usuario?.rotas_permitidas ?? [];

  const navItem = (destino: RotaPainel, label: string, icone?: string) => {
    if (!podeAcessarRota(destino, permitidas)) return null;
    return (
      <button
        type="button"
        className={`painel-nav-item ${rota === destino ? "ativo" : ""}`}
        onClick={() => onNavegar(destino)}
      >
        {icone && <span className="painel-nav-ico">{icone}</span>}
        {label}
      </button>
    );
  };

  const temAdmin =
    podeAcessarRota("robo", permitidas) ||
    podeAcessarRota("configuracoes", permitidas) ||
    podeAcessarRota("usuarios", permitidas) ||
    podeAcessarRota("auditoria", permitidas);

  return (
    <div className="painel-layout">
      <aside className="painel-sidebar">
        <div className="painel-sidebar-logo">leiautes_bacen</div>
        <nav className="painel-nav">
          {navItem("dashboard", "Dashboard", "📊")}
          {navItem("leiautes", "Leiautes", "📄")}
          {navItem("alteracoes", "Histórico e Versões", "🔎")}
          {temAdmin && (
            <>
              <div className="painel-nav-label">Administração</div>
              <div className="painel-nav-sub">
                {navItem("robo", "Robô")}
                {navItem("configuracoes", "Configurações")}
                {navItem("usuarios", "Usuários e perfis")}
                {navItem("auditoria", "Trilha de auditoria")}
              </div>
            </>
          )}
        </nav>
      </aside>
      <div className="painel-main-wrap">
        <header className="painel-topbar">
          <MenuUsuario
            onPerfil={() => onNavegar("perfil")}
            onSair={() => void sair()}
          />
        </header>
        <main className="painel-content">{children}</main>
        <footer className="painel-footer">© 2026 — leiautes_bacen</footer>
      </div>
    </div>
  );
}
