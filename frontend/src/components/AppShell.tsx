import { useEffect, useRef, useState, type ReactNode } from "react";
import { useAuth } from "../context/AuthContext";

export type RotaPainel =
  | "dashboard"
  | "leiautes"
  | "alteracoes"
  | "email"
  | "robo"
  | "configuracoes"
  | "usuarios"
  | "auditoria"
  | "alterar-senha";

type Props = {
  rota: RotaPainel;
  onNavegar: (rota: RotaPainel) => void;
  children: ReactNode;
};

function iniciaisUsuario(nome: string, email: string): string {
  const partes = nome.trim().split(/\s+/).filter(Boolean);
  if (partes.length >= 2) {
    return `${partes[0][0] ?? ""}${partes[partes.length - 1][0] ?? ""}`.toUpperCase();
  }
  if (nome.trim().length >= 2) return nome.trim().slice(0, 2).toUpperCase();
  return email.slice(0, 2).toUpperCase();
}

function MenuUsuario({
  onAlterarSenha,
  onSair,
}: {
  onAlterarSenha: () => void;
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
    <div className="app-menu user-menu-painel" ref={menuRef}>
      <button
        type="button"
        className="app-menu-trigger user-menu-trigger"
        aria-haspopup="menu"
        aria-expanded={menuAberto}
        onClick={() => setMenuAberto((v) => !v)}
      >
        <span className="user-avatar" aria-hidden>
          {iniciaisUsuario(usuario.nome, usuario.email)}
        </span>
        <span className="user-menu-email">
          {usuario.email}
          <span className="app-menu-chevron" aria-hidden>
            {" "}
            ▾
          </span>
        </span>
      </button>
      {menuAberto && (
        <ul className="app-menu-list" role="menu">
          <li role="none">
            <button
              type="button"
              role="menuitem"
              className="app-menu-item"
              onClick={() => escolher(onAlterarSenha)}
            >
              Alterar senha
            </button>
          </li>
          <li role="none">
            <button
              type="button"
              role="menuitem"
              className="app-menu-item app-menu-item-perigo"
              onClick={() => escolher(() => void onSair())}
            >
              Sair
            </button>
          </li>
        </ul>
      )}
    </div>
  );
}

export default function AppShell({ rota, onNavegar, children }: Props) {
  const { sair } = useAuth();

  const navItem = (destino: RotaPainel, label: string, icone?: string) => (
    <button
      type="button"
      className={`painel-nav-item ${rota === destino ? "ativo" : ""}`}
      onClick={() => onNavegar(destino)}
    >
      {icone && <span className="painel-nav-ico">{icone}</span>}
      {label}
    </button>
  );

  return (
    <div className="painel-layout">
      <aside className="painel-sidebar">
        <div className="painel-sidebar-logo">leiautes_bacen</div>
        <nav className="painel-nav">
          {navItem("dashboard", "Dashboard", "📊")}
          {navItem("leiautes", "Leiautes", "📄")}
          {navItem("alteracoes", "Alterações", "🔎")}
          {navItem("email", "E-mail do gestor", "✉️")}
          <div className="painel-nav-label">Administração</div>
          <div className="painel-nav-sub">
            {navItem("robo", "Robô")}
            {navItem("configuracoes", "Configurações")}
            {navItem("usuarios", "Usuários e perfis")}
            {navItem("auditoria", "Trilha de auditoria")}
          </div>
        </nav>
      </aside>
      <div className="painel-main-wrap">
        <header className="painel-topbar">
          <MenuUsuario
            onAlterarSenha={() => onNavegar("alterar-senha")}
            onSair={() => void sair()}
          />
        </header>
        <main className="painel-content">{children}</main>
        <footer className="painel-footer">© 2026 — leiautes_bacen</footer>
      </div>
    </div>
  );
}
