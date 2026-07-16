export type ExecucaoResumo = {
  id: number;
  iniciado_em: string;
  finalizado_em?: string | null;
  status: string;
  qtd_leiautes: number;
  qtd_arquivos: number;
  qtd_alteracoes: number;
  emails_enviados: number;
  erro?: string | null;
  log_path?: string | null;
};

export type AlteracaoResumo = {
  id: number;
  execucao_id: number;
  leiaute_codigo: string;
  arquivo_nome: string;
  arquivo_tipo: string;
  resumo_executivo: string;
  impacto_sugerido: string;
  status: string;
  criado_em: string;
  itens_incluidos: string[];
  itens_removidos: string[];
  itens_alterados: string[];
};

export type DashboardResponse = {
  ultima_execucao?: ExecucaoResumo | null;
  qtd_leiautes: number;
  qtd_arquivos: number;
  qtd_alteracoes: number;
  alteracoes_recentes: AlteracaoResumo[];
};

export type LeiauteResumo = {
  id: number;
  codigo: string;
  nome: string;
  categoria: string;
  url_bacen: string;
  tipos_arquivo: string[];
  ativo: boolean;
  ultima_leitura_em?: string | null;
};

export type LeiauteListaResponse = {
  total: number;
  leiautes: LeiauteResumo[];
};

export type ConfiguracoesResponse = {
  configuracoes: Record<string, unknown>;
};

export type ConfiguracoesMapa = Record<string, unknown>;

export type RoboStatusResponse = {
  script_motor: string;
  script_existe: boolean;
  ultima_execucao?: ExecucaoResumo | null;
};

export type UsuarioResumo = {
  id: number;
  email: string;
  nome: string;
  perfil_codigo: string;
  cargo?: string | null;
  departamento?: string | null;
  ativo: boolean;
};

export type UsuarioListaResponse = {
  total: number;
  usuarios: UsuarioResumo[];
};

export type PermissoesPerfilResponse = {
  permissoes: Record<string, string[]>;
};
