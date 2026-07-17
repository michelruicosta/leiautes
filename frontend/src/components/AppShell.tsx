import type { ReactNode } from "react";

export type RotaPainel =
  | "dashboard"
  | "leiautes"
  | "alteracoes"
  | "email"
  | "robo"
  | "configuracoes"
  | "usuarios"
  | "auditoria";

type Props = {
  rota: RotaPainel;
  onNavegar: (rota: RotaPainel) => void;
  children: ReactNode;
};

export default function AppShell({ rota, onNavegar, children }: Props) {
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
          <div className="user-menu-trigger">
            <span className="user-avatar">BG</span>
            <span className="user-menu-email">gestor@finaud.com.br ▾</span>
          </div>
        </header>
        <main className="painel-content">{children}</main>
        <footer className="painel-footer">© 2026 — leiautes_bacen</footer>
      </div>
    </div>
  );
}
