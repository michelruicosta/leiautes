import { useEffect, useRef, useState, type ReactNode } from "react";
import { useAuth, urlPortalApps } from "../context/AuthContext";
import {
  useTheme,
  type PreferenciaTema,
} from "../context/ThemeContext";

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
  leiautes: "admin-leiautes",
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

const OPCOES_TEMA: { id: PreferenciaTema; rotulo: string; dica: string }[] = [
  { id: "claro", rotulo: "Claro", dica: "Fundo claro" },
  { id: "escuro", rotulo: "Escuro", dica: "Fundo escuro" },
];

function MenuUsuario({
  onSair,
}: {
  onSair: () => void;
}) {
  const { usuario } = useAuth();
  const { preferencia, setPreferencia } = useTheme();
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

  const iniciais = usuario.nome
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");

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
        <div className="app-menu-list" role="menu">
          <div className="app-menu-info">
            <div className="user-avatar" aria-hidden>
              {iniciais || "?"}
            </div>
            <div className="app-menu-info-textos">
              <div className="app-menu-info-nome">{usuario.nome}</div>
              {usuario.email ? (
                <div className="app-menu-info-email">{usuario.email}</div>
              ) : null}
            </div>
          </div>

          <div className="app-menu-section">
            <div className="app-menu-section-title">Aparência</div>
            <div className="app-theme-opts" role="group" aria-label="Aparência">
              {OPCOES_TEMA.map((op) => (
                <button
                  key={op.id}
                  type="button"
                  className={`app-theme-btn${preferencia === op.id ? " ativo" : ""}`}
                  aria-pressed={preferencia === op.id}
                  title={op.dica}
                  onClick={() => setPreferencia(op.id)}
                >
                  {op.rotulo}
                </button>
              ))}
            </div>
          </div>

          <a
            role="menuitem"
            className="app-menu-item app-menu-link"
            href={urlPortalApps()}
            target="_blank"
            rel="noopener noreferrer"
            onClick={() => setMenuAberto(false)}
          >
            Portal de apps
          </a>
          <button
            type="button"
            role="menuitem"
            className="app-menu-item app-menu-item-perigo"
            onClick={() => escolher(onSair)}
          >
            Sair
          </button>
        </div>
      )}
    </div>
  );
}

export function podeAcessarRota(
  rota: RotaPainel,
  rotasPermitidas: string[] | undefined,
): boolean {
  if (rota === "alterar-senha" || rota === "perfil") return false;
  const codigo = ROTA_PARA_PERMISSAO[rota];
  return (rotasPermitidas ?? []).includes(codigo);
}

export default function AppShell({ rota, onNavegar, children }: Props) {
  const { usuario, sair } = useAuth();
  const permitidas = usuario?.rotas_permitidas ?? [];

  const [operacaoAberta, setOperacaoAberta] = useState(
    rota === "dashboard" || rota === "alteracoes",
  );
  const [adminAberta, setAdminAberta] = useState(
    rota === "leiautes" ||
      rota === "robo" ||
      rota === "configuracoes" ||
      rota === "usuarios" ||
      rota === "auditoria",
  );
  const [sidebarRecolhida, setSidebarRecolhida] = useState(false);

  useEffect(() => {
    if (rota === "dashboard" || rota === "alteracoes") {
      setOperacaoAberta(true);
    }
    if (
      rota === "leiautes" ||
      rota === "robo" ||
      rota === "configuracoes" ||
      rota === "usuarios" ||
      rota === "auditoria"
    ) {
      setAdminAberta(true);
    }
  }, [rota]);

  const navItem = (destino: RotaPainel, label: string, icone: string) => {
    if (!podeAcessarRota(destino, permitidas)) return null;
    return (
      <button
        type="button"
        className={`painel-nav-item ${rota === destino ? "ativo" : ""}`}
        onClick={() => onNavegar(destino)}
        title={label}
        aria-label={label}
      >
        <span className="painel-nav-ico" aria-hidden>
          {icone}
        </span>
        <span className="painel-nav-texto">{label}</span>
      </button>
    );
  };

  const grupoNav = (
    id: string,
    titulo: string,
    aberto: boolean,
    onToggle: () => void,
    itens: ReactNode,
  ) => (
    <div className="painel-nav-grupo">
      <button
        type="button"
        className="painel-nav-label painel-nav-label-btn"
        aria-expanded={aberto}
        aria-controls={id}
        onClick={onToggle}
      >
        <span className="painel-nav-label-texto">{titulo}</span>
        <span className="painel-nav-label-chevron" aria-hidden>
          {aberto ? "▾" : "▸"}
        </span>
      </button>
      {aberto && (
        <div className="painel-nav-sub" id={id}>
          {itens}
        </div>
      )}
    </div>
  );

  const temOperacao =
    podeAcessarRota("dashboard", permitidas) ||
    podeAcessarRota("alteracoes", permitidas);

  const temAdmin =
    podeAcessarRota("leiautes", permitidas) ||
    podeAcessarRota("robo", permitidas) ||
    podeAcessarRota("configuracoes", permitidas) ||
    podeAcessarRota("usuarios", permitidas) ||
    podeAcessarRota("auditoria", permitidas);

  const itensOperacao = (
    <>
      {navItem("dashboard", "Monitoramento", "📊")}
      {navItem("alteracoes", "Histórico e Versões", "🔎")}
    </>
  );

  const itensAdmin = (
    <>
      {navItem("leiautes", "Cadastro de Leiautes", "📄")}
      {navItem("robo", "Robô", "🤖")}
      {navItem("configuracoes", "Configurações", "⚙️")}
      {navItem("usuarios", "Usuários e perfis", "👤")}
      {navItem("auditoria", "Trilha de auditoria", "📋")}
    </>
  );

  return (
    <div
      className={`painel-layout${sidebarRecolhida ? " painel-sidebar-recolhida" : ""}`}
    >
      <aside className="painel-sidebar">
        <div className="painel-sidebar-topo">
          <div className="painel-sidebar-logo" title="Leiautes Bacen">
            <span className="painel-sidebar-logo-full">Leiautes Bacen</span>
            <span className="painel-sidebar-logo-curto" aria-hidden>
              LB
            </span>
          </div>
          <button
            type="button"
            className="painel-sidebar-toggle"
            onClick={() => setSidebarRecolhida((v) => !v)}
            title={sidebarRecolhida ? "Expandir menu" : "Recolher menu"}
            aria-label={sidebarRecolhida ? "Expandir menu" : "Recolher menu"}
          >
            {sidebarRecolhida ? "»" : "«"}
          </button>
        </div>
        <nav className="painel-nav">
          {sidebarRecolhida ? (
            <>
              {itensOperacao}
              {temAdmin && itensAdmin}
            </>
          ) : (
            <>
              {temOperacao &&
                grupoNav(
                  "nav-operacao",
                  "Operação",
                  operacaoAberta,
                  () => setOperacaoAberta((v) => !v),
                  itensOperacao,
                )}
              {temAdmin &&
                grupoNav(
                  "nav-admin",
                  "Administração",
                  adminAberta,
                  () => setAdminAberta((v) => !v),
                  itensAdmin,
                )}
            </>
          )}
        </nav>
      </aside>
      <div className="painel-main-wrap">
        <header className="painel-topbar">
          <MenuUsuario onSair={() => void sair()} />
        </header>
        <main className="painel-content">{children}</main>
        <footer className="painel-footer">© 2026 — Leiautes Bacen</footer>
      </div>
    </div>
  );
}
