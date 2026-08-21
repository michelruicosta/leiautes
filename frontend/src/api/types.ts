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

export type ExecucaoListaResponse = {
  total: number;
  execucoes: ExecucaoResumo[];
};

export type ExecucaoLogResponse = {
  execucao: ExecucaoResumo;
  log_texto: string;
  log_path?: string | null;
  disponivel: boolean;
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

export type AlteracaoListaResponse = {
  total: number;
  limit: number;
  offset: number;
  alteracoes: AlteracaoResumo[];
};

export type VersaoArquivoResumo = {
  id: number;
  capturado_em: string;
  leiaute_codigo: string;
  arquivo_nome: string;
  arquivo_tipo: string;
  vigencia: string;
  fora_do_site: boolean;
};

export type VersaoArquivoListaResponse = {
  total: number;
  limit: number;
  offset: number;
  versoes: VersaoArquivoResumo[];
};

export type DashboardResponse = {
  ultima_execucao?: ExecucaoResumo | null;
  qtd_leiautes: number;
  qtd_arquivos: number;
  qtd_alteracoes: number;
  qtd_entrou: number;
  qtd_mudou: number;
  qtd_saiu: number;
  arquivos_destaque: {
    leiaute_codigo: string;
    arquivo_nome: string;
    arquivo_tipo: string;
    total_evidencias: number;
  }[];
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

export type LeiautePayload = {
  codigo: string;
  nome: string;
  categoria: string;
  url_bacen: string;
  tipos_arquivo: string[];
  ativo: boolean;
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

export type RoboExecutarResponse = {
  execucao_id: number;
  status: string;
  returncode: number;
  stdout_tail: string;
  stderr_tail: string;
};

export type AgendaRobo = {
  horarios: string[];
  dias_semana: number[];
  feriados: string[];
  robo_ativo: boolean;
  atualizado_em?: string | null;
};

export type UsuarioResumo = {
  id: number;
  email: string;
  nome: string;
  perfil_codigo: string;
  cargo?: string | null;
  departamento?: string | null;
  ativo: boolean;
  receber_email_alertas: boolean;
};

export type UsuarioPayload = {
  email: string;
  nome: string;
  perfil_codigo: "operador" | "gestor" | "administrador";
  senha_inicial?: string;
  nova_senha?: string;
  cargo?: string | null;
  departamento?: string | null;
  ativo: boolean;
  receber_email_alertas: boolean;
};

export type UsuarioListaResponse = {
  total: number;
  usuarios: UsuarioResumo[];
};

export type PermissoesPerfilResponse = {
  permissoes: Record<string, string[]>;
};

export type LogAuditoria = {
  id: number;
  usuario: string;
  pagina: string;
  acao: string;
  detalhe: string;
  criado_em: string;
};

export type LogAuditoriaListaResponse = {
  total: number;
  registros: LogAuditoria[];
};

export type EmailGestorPreviewResponse = {
  assunto: string;
  destinatarios: string[];
  copia: string[];
  resumo: string;
  alteracoes: AlteracaoResumo[];
  anexos: string[];
};
