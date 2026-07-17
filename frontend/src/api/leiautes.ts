import { apiGet, apiPut, apiUrl } from "./client";
import type {
  ConfiguracoesResponse,
  DashboardResponse,
  EmailGestorPreviewResponse,
  AlteracaoListaResponse,
  LeiauteListaResponse,
  PermissoesPerfilResponse,
  RoboStatusResponse,
  UsuarioListaResponse,
} from "./types";

export function obterDashboard() {
  return apiGet<DashboardResponse>("/dashboard");
}

export function listarLeiautes() {
  return apiGet<LeiauteListaResponse>("/leiautes");
}

export function listarAlteracoes() {
  return apiGet<AlteracaoListaResponse>("/alteracoes");
}

export function urlRelatorioAlteracoes(escopo: "ultima" | "historico") {
  return apiUrl(`/relatorios/alteracoes.xlsx?escopo=${escopo}`);
}

export function obterConfiguracoes() {
  return apiGet<ConfiguracoesResponse>("/configuracoes");
}

export function salvarConfiguracoes(configuracoes: Record<string, unknown>) {
  return apiPut<ConfiguracoesResponse>("/configuracoes", { configuracoes });
}

export function obterStatusRobo() {
  return apiGet<RoboStatusResponse>("/robo/status");
}

export function obterPreviewEmailGestor() {
  return apiGet<EmailGestorPreviewResponse>("/email-gestor/preview");
}

export function listarUsuarios() {
  return apiGet<UsuarioListaResponse>("/usuarios");
}

export function obterPermissoesPerfis() {
  return apiGet<PermissoesPerfilResponse>("/usuarios/perfis/permissoes");
}

export function salvarPermissoesPerfis(permissoes: Record<string, string[]>) {
  return apiPut<PermissoesPerfilResponse>("/usuarios/perfis/permissoes", {
    permissoes,
  });
}
