import { apiDownload, apiGet, apiPost, apiPut, apiUrl } from "./client";
import type {
  ConfiguracoesResponse,
  DashboardResponse,
  EmailGestorPreviewResponse,
  ExecucaoListaResponse,
  ExecucaoLogResponse,
  AlteracaoListaResponse,
  LeiauteListaResponse,
  PermissoesPerfilResponse,
  RoboExecutarResponse,
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

export function baixarRelatorioAlteracoes(escopo: "ultima" | "historico") {
  const fallback =
    escopo === "ultima"
      ? "relatorio_alteracoes_leiautes_envio.xlsx"
      : "relatorio_alteracoes_leiautes_historico.xlsx";
  return apiDownload(`/relatorios/alteracoes.xlsx?escopo=${escopo}`, fallback);
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

export function executarRoboSemEmail() {
  return apiPost<RoboExecutarResponse>("/robo/executar", {
    modo_teste: false,
    enviar_email: false,
  });
}

export function listarExecucoes(limit = 50, offset = 0) {
  return apiGet<ExecucaoListaResponse>(`/execucoes?limit=${limit}&offset=${offset}`);
}

export function obterLogExecucao(execucaoId: number) {
  return apiGet<ExecucaoLogResponse>(`/execucoes/${execucaoId}/log`);
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
