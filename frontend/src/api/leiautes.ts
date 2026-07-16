import { apiGet, apiPut } from "./client";
import type {
  ConfiguracoesResponse,
  DashboardResponse,
  LeiauteListaResponse,
  RoboStatusResponse,
} from "./types";

export function obterDashboard() {
  return apiGet<DashboardResponse>("/dashboard");
}

export function listarLeiautes() {
  return apiGet<LeiauteListaResponse>("/leiautes");
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
