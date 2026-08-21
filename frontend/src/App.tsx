import { useEffect, useState } from "react";
import AppShell, { podeAcessarRota, type RotaPainel } from "./components/AppShell";
import AlteracoesPage from "./pages/AlteracoesPage";
import AlterarSenhaPage from "./pages/AlterarSenhaPage";
import AuditoriaPage from "./pages/AuditoriaPage";
import ConfiguracoesPage from "./pages/ConfiguracoesPage";
import DashboardPage from "./pages/DashboardPage";
import LeiautesPage from "./pages/LeiautesPage";
import LoginPage from "./pages/LoginPage";
import PerfilPage from "./pages/PerfilPage";
import RoboPage from "./pages/RoboPage";
import UsuariosPage from "./pages/UsuariosPage";
import { useAuth } from "./context/AuthContext";

export default function App() {
  const { usuario, carregando } = useAuth();
  const [rota, setRota] = useState<RotaPainel>("dashboard");

  useEffect(() => {
    if (!usuario) return;
    if (!podeAcessarRota(rota, usuario.rotas_permitidas)) {
      setRota("dashboard");
    }
  }, [usuario, rota]);

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

  const rotaEfetiva = podeAcessarRota(rota, usuario.rotas_permitidas)
    ? rota
    : "dashboard";

  const pagina =
    rotaEfetiva === "dashboard" ? (
      <DashboardPage />
    ) : rotaEfetiva === "leiautes" ? (
      <LeiautesPage />
    ) : rotaEfetiva === "robo" ? (
      <RoboPage />
    ) : rotaEfetiva === "alteracoes" ? (
      <AlteracoesPage />
    ) : rotaEfetiva === "configuracoes" ? (
      <ConfiguracoesPage />
    ) : rotaEfetiva === "auditoria" ? (
      <AuditoriaPage />
    ) : rotaEfetiva === "perfil" ? (
      <PerfilPage
        onAlterarSenha={() => setRota("alterar-senha")}
        onVoltarHome={() => setRota("dashboard")}
      />
    ) : rotaEfetiva === "alterar-senha" ? (
      <AlterarSenhaPage onVoltarPerfil={() => setRota("perfil")} />
    ) : (
      <UsuariosPage />
    );

  return (
    <AppShell rota={rotaEfetiva} onNavegar={setRota}>
      {pagina}
    </AppShell>
  );
}
