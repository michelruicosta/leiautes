import { apiPost } from "./client";

export type UsuarioAuth = {
  id: number;
  email: string;
  nome: string;
  perfil_codigo: string;
  cargo?: string | null;
  departamento?: string | null;
  rotas_permitidas: string[];
};

export type LoginResponse = {
  usuario: UsuarioAuth;
  mensagem: string;
};

export function loginAuth(email: string, senha: string) {
  return apiPost<LoginResponse>("/auth/login", { email, senha });
}

export function recuperarSenhaAuth(email: string) {
  return apiPost<{ mensagem: string }>("/auth/recuperar-senha", { email });
}

