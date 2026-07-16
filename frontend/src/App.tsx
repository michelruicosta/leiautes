import { useState } from "react";
import AppShell, { type RotaPainel } from "./components/AppShell";
import ConfiguracoesPage from "./pages/ConfiguracoesPage";
import DashboardPage from "./pages/DashboardPage";
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
      <DashboardPage />
    ) : rota === "leiautes" ? (
      <LeiautesPage />
    ) : rota === "robo" ? (
      <RoboPage />
    ) : rota === "alteracoes" ? (
      <PlaceholderPage
        titulo="Alterações"
        subtitulo="Histórico e comparação entre a versão anterior e atual."
      />
    ) : rota === "email" ? (
      <PlaceholderPage
        titulo="E-mail do gestor"
        subtitulo="Prévia do comunicado com resumo executivo das diferenças."
      />
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
