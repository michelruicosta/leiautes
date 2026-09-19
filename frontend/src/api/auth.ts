import { apiGet, apiPost } from "./client";

export type UsuarioAuth = {
  id: number;
  email: string;
  nome: string;
  perfil_codigo: string;
  cargo?: string | null;
  departamento?: string | null;
  rotas_permitidas: string[];
};

export async function logoutAuth(): Promise<void> {
  await apiPost<void>("/auth/logout", {});
}

export function obterUsuarioAtual() {
  return apiGet<UsuarioAuth>("/auth/me");
}
