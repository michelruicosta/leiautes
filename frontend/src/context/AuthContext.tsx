import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  loginAuth,
  logoutAuth,
  obterUsuarioAtual,
  type UsuarioAuth,
} from "../api/auth";
import { ApiError } from "../api/client";

type AuthContextValue = {
  usuario: UsuarioAuth | null;
  carregando: boolean;
  entrar: (email: string, senha: string) => Promise<void>;
  sair: () => Promise<void>;
  recarregar: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<UsuarioAuth | null>(null);
  const [carregando, setCarregando] = useState(true);

  const recarregar = useCallback(async () => {
    try {
      const u = await obterUsuarioAtual();
      setUsuario(u);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        setUsuario(null);
        return;
      }
      setUsuario(null);
    }
  }, []);

  useEffect(() => {
    void (async () => {
      setCarregando(true);
      await recarregar();
      setCarregando(false);
    })();
  }, [recarregar]);

  const entrar = useCallback(async (email: string, senha: string) => {
    const resposta = await loginAuth(email, senha);
    setUsuario(resposta.usuario);
  }, []);

  const sair = useCallback(async () => {
    try {
      await logoutAuth();
    } finally {
      setUsuario(null);
    }
  }, []);

  const value = useMemo(
    () => ({ usuario, carregando, entrar, sair, recarregar }),
    [usuario, carregando, entrar, sair, recarregar],
  );

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth deve ser usado dentro de AuthProvider");
  }
  return ctx;
}
