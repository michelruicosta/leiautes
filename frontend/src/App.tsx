import { useState } from "react";
import AppShell, { type RotaPainel } from "./components/AppShell";
import AlteracoesPage from "./pages/AlteracoesPage";
import ConfiguracoesPage from "./pages/ConfiguracoesPage";
import DashboardPage from "./pages/DashboardPage";
import EmailGestorPage from "./pages/EmailGestorPage";
import LeiautesPage from "./pages/LeiautesPage";
import LoginPage from "./pages/LoginPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import RoboPage from "./pages/RoboPage";
import UsuariosPage from "./pages/UsuariosPage";

export default function App() {
  const [autenticado, setAutenticado] = useState(false);
  const [rota, setRota] = useState<RotaPainel>("dashboard");

  if (!autenticado) {
    return <LoginPage onEntrar={() => setAutenticado(true)} />;
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
    ) : (
      <UsuariosPage />
    );

  return (
    <AppShell rota={rota} onNavegar={setRota}>
      {pagina}
    </AppShell>
  );
}
