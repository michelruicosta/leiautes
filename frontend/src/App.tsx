import { useState } from "react";
import AppShell, { type RotaPainel } from "./components/AppShell";
import AlteracoesPage from "./pages/AlteracoesPage";
import AlterarSenhaPage from "./pages/AlterarSenhaPage";
import AuditoriaPage from "./pages/AuditoriaPage";
import ConfiguracoesPage from "./pages/ConfiguracoesPage";
import DashboardPage from "./pages/DashboardPage";
import EmailGestorPage from "./pages/EmailGestorPage";
import LeiautesPage from "./pages/LeiautesPage";
import LoginPage from "./pages/LoginPage";
import RoboPage from "./pages/RoboPage";
import UsuariosPage from "./pages/UsuariosPage";
import { useAuth } from "./context/AuthContext";

export default function App() {
  const { usuario, carregando } = useAuth();
  const [rota, setRota] = useState<RotaPainel>("dashboard");

  if (carregando) {
    return (
      <div className="login-shell">
        <p className="meta">Carregando…</p>
      </div>
    );
  }

  if (!usuario) {
    return <LoginPage />;
  }

  const pagina =
    rota === "dashboard" ? (
      <DashboardPage onExecutarRobo={() => setRota("robo")} />
    ) : rota === "leiautes" ? (
      <LeiautesPage />
    ) : rota === "robo" ? (
      <RoboPage />
    ) : rota === "alteracoes" ? (
      <AlteracoesPage />
    ) : rota === "email" ? (
      <EmailGestorPage />
    ) : rota === "configuracoes" ? (
      <ConfiguracoesPage />
    ) : rota === "auditoria" ? (
      <AuditoriaPage />
    ) : rota === "alterar-senha" ? (
      <AlterarSenhaPage onVoltar={() => setRota("dashboard")} />
    ) : (
      <UsuariosPage />
    );

  return (
    <AppShell rota={rota} onNavegar={setRota}>
      {pagina}
    </AppShell>
  );
}
