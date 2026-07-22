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

export type LoginResponse = {
  usuario: UsuarioAuth;
  mensagem: string;
};

export function loginAuth(email: string, senha: string) {
  return apiPost<LoginResponse>("/auth/login", { email, senha });
}

export async function logoutAuth(): Promise<void> {
  await apiPost<void>("/auth/logout", {});
}

export function obterUsuarioAtual() {
  return apiGet<UsuarioAuth>("/auth/me");
}

export function recuperarSenhaAuth(email: string) {
  return apiPost<{ mensagem: string }>("/auth/recuperar-senha", { email });
}

export function alterarSenhaAuth(
  senhaAtual: string,
  novaSenha: string,
  confirmarSenha: string,
) {
  return apiPost<{ mensagem: string }>("/auth/alterar-senha", {
    senha_atual: senhaAtual,
    nova_senha: novaSenha,
    confirmar_senha: confirmarSenha,
  });
}
