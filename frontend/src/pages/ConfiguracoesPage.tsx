import { type FormEvent, useEffect, useMemo, useState } from "react";
import {
  obterConfiguracoes,
  salvarConfiguracoes,
} from "../api/leiautes";
import type { ConfiguracoesMapa } from "../api/types";

type AbaConfig =
  | "empresa"
  | "email"
  | "monitoramento"
  | "anexos"
  | "comparacao"
  | "status";

const ABAS: { id: AbaConfig; label: string }[] = [
  { id: "empresa", label: "Empresa" },
  { id: "email", label: "E-mail" },
  { id: "monitoramento", label: "Monitoramento" },
  { id: "anexos", label: "Anexos" },
  { id: "comparacao", label: "Comparação" },
  { id: "status", label: "Status público" },
];

const DEFAULTS: ConfiguracoesMapa = {
  "empresa.nome": "FINAUD TEC",
  "empresa.cor_marca": "#3333a8",
  "empresa.subtitulo": "Leiautes Bacen - Monitoramento",
  "email.remetente": "",
  "email.assunto": "Atualização em leiautes Bacen - {data}",
  "email.destinatarios": [],
  "email.copia": [],
  "email.smtp_servidor": "smtp.gmail.com",
  "email.smtp_porta": 465,
  "email.enviar_sem_alteracao": true,
  "email.anexar_alterados": true,
  "monitor.connect_timeout": 10,
  "monitor.read_timeout": 10,
  "monitor.only_atual": true,
  "monitor.quiet_baseline": false,
  "monitor.exclude_patterns": ["versoes_anteriores", "anteriores", "historico"],
  "anexos.max_attachments": 8,
  "anexos.max_single_mb": 4,
  "anexos.max_total_mb": 18,
  "anexos.extensoes": ["pdf", "xls", "xlsx", "xsd", "zip"],
  "comparacao.nivel_resumo": "executivo_tecnico",
  "comparacao.max_diferencas_email": 12,
  "comparacao.prompt_resumo":
    "Explique ao gestor o impacto prático da alteração, separando inclusões, remoções e mudanças relevantes.",
  "status.tail_path":
    "/home/tsalachtech.com.br/public_html/monitoramentos/leiautes/_status_tail.txt",
  "status.log_dir": "/home/tsalachtech.com.br/apps/leiautes/logs",
  "status.manifest_path": "dados/manifest_arquivos.json",
  "status.storage_dir": "storage/arquivos",
};

function textoLista(valor: unknown): string {
  if (Array.isArray(valor)) return valor.join("\n");
  if (typeof valor === "string") return valor;
  return "";
}

function listaTexto(texto: string): string[] {
  return texto
    .split(/[\n,;]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function boolValor(valor: unknown): boolean {
  return valor === true || valor === "true" || valor === 1;
}

function numeroValor(valor: unknown, fallback: number): number {
  const n = Number(valor);
  return Number.isFinite(n) ? n : fallback;
}

export default function ConfiguracoesPage() {
  const [aba, setAba] = useState<AbaConfig>("empresa");
  const [form, setForm] = useState<ConfiguracoesMapa>(DEFAULTS);
  const [erro, setErro] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    setCarregando(true);
    obterConfiguracoes()
      .then((resp) => setForm({ ...DEFAULTS, ...resp.configuracoes }))
      .catch(() => setErro("API indisponível. Mostrando valores padrão."))
      .finally(() => setCarregando(false));
  }, []);

  const corMarca = useMemo(
    () => String(form["empresa.cor_marca"] ?? "#3333a8"),
    [form],
  );

  const setCampo = (chave: string, valor: unknown) => {
    setForm((atual) => ({ ...atual, [chave]: valor }));
  };

  const validar = (): string | null => {
    const cor = String(form["empresa.cor_marca"] ?? "");
    if (!/^#[0-9a-fA-F]{6}$/.test(cor)) return "Informe uma cor hexadecimal válida.";
    if (numeroValor(form["email.smtp_porta"], 0) <= 0) return "Informe uma porta SMTP válida.";
    if (numeroValor(form["monitor.connect_timeout"], 0) <= 0) {
      return "Informe um timeout de conexão maior que zero.";
    }
    if (numeroValor(form["monitor.read_timeout"], 0) <= 0) {
      return "Informe um timeout de leitura maior que zero.";
    }
    if (numeroValor(form["anexos.max_attachments"], 0) <= 0) {
      return "Informe a quantidade máxima de anexos.";
    }
    if (numeroValor(form["anexos.max_single_mb"], 0) <= 0) {
      return "Informe o tamanho máximo por arquivo.";
    }
    if (numeroValor(form["anexos.max_total_mb"], 0) <= 0) {
      return "Informe o tamanho máximo total do e-mail.";
    }
    if (listaTexto(textoLista(form["anexos.extensoes"])).length === 0) {
      return "Informe ao menos uma extensão monitorada.";
    }
    return null;
  };

  const salvar = async (e: FormEvent) => {
    e.preventDefault();
    setErro(null);
    setMsg(null);
    const problema = validar();
    if (problema) {
      setErro(problema);
      return;
    }
    setSalvando(true);
    try {
      const resp = await salvarConfiguracoes(form);
      setForm({ ...DEFAULTS, ...resp.configuracoes });
      setMsg("Configurações salvas.");
    } catch {
      setErro("Não foi possível salvar as configurações.");
    } finally {
      setSalvando(false);
    }
  };

  return (
    <div className="admin-page">
      <form onSubmit={(e) => void salvar(e)}>
        <div className="page-cabecalho">
          <div>
            <h1 className="page-title">Configurações</h1>
            <p className="page-sub">
              Parâmetros do robô, e-mail, comparação e caminhos operacionais.
            </p>
          </div>
          <button type="submit" className="btn-novo" disabled={salvando}>
            {salvando ? "Salvando..." : "Salvar alterações"}
          </button>
        </div>

        <div className="admin-tabs config-abas" role="tablist">
          {ABAS.map((item) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              className={aba === item.id ? "ativo" : ""}
              aria-selected={aba === item.id}
              onClick={() => setAba(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>

        {erro && <p className="erro">{erro}</p>}
        {msg && <p className="login-sucesso">{msg}</p>}
        {carregando && <p className="meta">Carregando...</p>}

        <section className="config-painel-aba">
          {aba === "empresa" && (
            <>
              <p className="admin-ajuda">
                Nome, subtítulo e cor usados na tela de login, menu lateral e e-mails.
              </p>
              <div className="config-marca-linha">
                <div className="config-logo-preview" style={{ color: corMarca }}>
                  FT
                </div>
                <div className="config-logo-acoes">
                  <button type="button" className="btn-secondary" disabled>
                    Envio de logo pendente
                  </button>
                  <p className="meta">A etapa de upload da logo entra com autenticação.</p>
                </div>
              </div>
              <div className="field">
                <label className="field-label">Nome da empresa</label>
                <input
                  className="field-input"
                  value={String(form["empresa.nome"] ?? "")}
                  onChange={(e) => setCampo("empresa.nome", e.target.value)}
                />
              </div>
              <div className="field">
                <label className="field-label">Subtítulo do sistema</label>
                <input
                  className="field-input"
                  value={String(form["empresa.subtitulo"] ?? "")}
                  onChange={(e) => setCampo("empresa.subtitulo", e.target.value)}
                />
              </div>
              <div className="config-dupla">
                <div className="field">
                  <label className="field-label">Cor da empresa</label>
                  <input
                    className="config-cor-picker"
                    type="color"
                    value={corMarca}
                    onChange={(e) => setCampo("empresa.cor_marca", e.target.value)}
                  />
                </div>
                <div className="field">
                  <label className="field-label">Hexadecimal</label>
                  <input
                    className="field-input"
                    value={corMarca}
                    onChange={(e) => setCampo("empresa.cor_marca", e.target.value)}
                  />
                </div>
              </div>
            </>
          )}

          {aba === "email" && (
            <>
              <p className="admin-ajuda">
                Conta, destinatários e comportamento do envio automático.
              </p>
              <div className="config-dupla">
                <div className="field">
                  <label className="field-label">Remetente</label>
                  <input
                    className="field-input"
                    value={String(form["email.remetente"] ?? "")}
                    onChange={(e) => setCampo("email.remetente", e.target.value)}
                  />
                </div>
                <div className="field">
                  <label className="field-label">Assunto padrão</label>
                  <input
                    className="field-input"
                    value={String(form["email.assunto"] ?? "")}
                    onChange={(e) => setCampo("email.assunto", e.target.value)}
                  />
                </div>
              </div>
              <div className="config-dupla">
                <div className="field">
                  <label className="field-label">Servidor SMTP</label>
                  <input
                    className="field-input"
                    value={String(form["email.smtp_servidor"] ?? "")}
                    onChange={(e) => setCampo("email.smtp_servidor", e.target.value)}
                  />
                </div>
                <div className="field">
                  <label className="field-label">Porta</label>
                  <input
                    className="field-input"
                    type="number"
                    value={numeroValor(form["email.smtp_porta"], 465)}
                    onChange={(e) => setCampo("email.smtp_porta", Number(e.target.value))}
                  />
                </div>
              </div>
              <label className="field">
                <span className="field-label">Destinatários principais</span>
                <textarea
                  className="field-input admin-textarea"
                  value={textoLista(form["email.destinatarios"])}
                  onChange={(e) => setCampo("email.destinatarios", listaTexto(e.target.value))}
                />
              </label>
              <label className="field">
                <span className="field-label">Cópia opcional</span>
                <textarea
                  className="field-input admin-textarea"
                  value={textoLista(form["email.copia"])}
                  onChange={(e) => setCampo("email.copia", listaTexto(e.target.value))}
                />
              </label>
              <div className="admin-dias">
                <label className="admin-dia-chip">
                  <input
                    type="checkbox"
                    checked={boolValor(form["email.enviar_sem_alteracao"])}
                    onChange={(e) => setCampo("email.enviar_sem_alteracao", e.target.checked)}
                  />
                  Enviar mesmo sem alteração
                </label>
                <label className="admin-dia-chip">
                  <input
                    type="checkbox"
                    checked={boolValor(form["email.anexar_alterados"])}
                    onChange={(e) => setCampo("email.anexar_alterados", e.target.checked)}
                  />
                  Anexar arquivos alterados
                </label>
              </div>
            </>
          )}

          {aba === "monitoramento" && (
            <>
              <p className="admin-ajuda">
                Timeouts, filtros e regras gerais da leitura das páginas Bacen.
              </p>
              <div className="config-dupla">
                <div className="field">
                  <label className="field-label">Timeout de conexão, segundos</label>
                  <input
                    className="field-input"
                    type="number"
                    value={numeroValor(form["monitor.connect_timeout"], 10)}
                    onChange={(e) => setCampo("monitor.connect_timeout", Number(e.target.value))}
                  />
                </div>
                <div className="field">
                  <label className="field-label">Timeout de leitura, segundos</label>
                  <input
                    className="field-input"
                    type="number"
                    value={numeroValor(form["monitor.read_timeout"], 10)}
                    onChange={(e) => setCampo("monitor.read_timeout", Number(e.target.value))}
                  />
                </div>
              </div>
              <div className="admin-dias">
                <label className="admin-dia-chip">
                  <input
                    type="checkbox"
                    checked={boolValor(form["monitor.only_atual"])}
                    onChange={(e) => setCampo("monitor.only_atual", e.target.checked)}
                  />
                  Apenas arquivos em /atual/
                </label>
                <label className="admin-dia-chip">
                  <input
                    type="checkbox"
                    checked={boolValor(form["monitor.quiet_baseline"])}
                    onChange={(e) => setCampo("monitor.quiet_baseline", e.target.checked)}
                  />
                  Primeira leitura sem e-mail
                </label>
              </div>
              <label className="field">
                <span className="field-label">Padrões excluídos</span>
                <textarea
                  className="field-input admin-textarea"
                  value={textoLista(form["monitor.exclude_patterns"])}
                  onChange={(e) => setCampo("monitor.exclude_patterns", listaTexto(e.target.value))}
                />
              </label>
            </>
          )}

          {aba === "anexos" && (
            <>
              <p className="admin-ajuda">
                Limites de anexos e extensões monitoradas.
              </p>
              <div className="config-dupla">
                <div className="field">
                  <label className="field-label">Máximo de anexos</label>
                  <input
                    className="field-input"
                    type="number"
                    value={numeroValor(form["anexos.max_attachments"], 8)}
                    onChange={(e) => setCampo("anexos.max_attachments", Number(e.target.value))}
                  />
                </div>
                <div className="field">
                  <label className="field-label">Máximo por arquivo, MB</label>
                  <input
                    className="field-input"
                    type="number"
                    value={numeroValor(form["anexos.max_single_mb"], 4)}
                    onChange={(e) => setCampo("anexos.max_single_mb", Number(e.target.value))}
                  />
                </div>
              </div>
              <div className="field">
                <label className="field-label">Máximo total do e-mail, MB</label>
                <input
                  className="field-input"
                  type="number"
                  value={numeroValor(form["anexos.max_total_mb"], 18)}
                  onChange={(e) => setCampo("anexos.max_total_mb", Number(e.target.value))}
                />
              </div>
              <label className="field">
                <span className="field-label">Extensões monitoradas</span>
                <textarea
                  className="field-input admin-textarea"
                  value={textoLista(form["anexos.extensoes"])}
                  onChange={(e) => setCampo("anexos.extensoes", listaTexto(e.target.value))}
                />
              </label>
            </>
          )}

          {aba === "comparacao" && (
            <>
              <p className="admin-ajuda">
                Critérios usados para montar o resumo executivo das diferenças.
              </p>
              <div className="config-dupla">
                <label className="field">
                  <span className="field-label">Nível do resumo</span>
                  <select
                    className="field-input"
                    value={String(form["comparacao.nivel_resumo"] ?? "executivo_tecnico")}
                    onChange={(e) => setCampo("comparacao.nivel_resumo", e.target.value)}
                  >
                    <option value="executivo_tecnico">Executivo + técnico</option>
                    <option value="executivo">Somente executivo</option>
                    <option value="tecnico">Somente técnico</option>
                  </select>
                </label>
                <label className="field">
                  <span className="field-label">Diferenças máximas no e-mail</span>
                  <input
                    className="field-input"
                    type="number"
                    value={numeroValor(form["comparacao.max_diferencas_email"], 12)}
                    onChange={(e) =>
                      setCampo("comparacao.max_diferencas_email", Number(e.target.value))
                    }
                  />
                </label>
              </div>
              <label className="field">
                <span className="field-label">Prompt/critério do resumo</span>
                <textarea
                  className="field-input admin-textarea textarea-alta"
                  value={String(form["comparacao.prompt_resumo"] ?? "")}
                  onChange={(e) => setCampo("comparacao.prompt_resumo", e.target.value)}
                />
              </label>
            </>
          )}

          {aba === "status" && (
            <>
              <p className="admin-ajuda">
                Caminhos operacionais usados pelo robô, logs e status público.
              </p>
              {[
                ["status.tail_path", "Arquivo de status público"],
                ["status.log_dir", "Pasta de logs"],
                ["status.manifest_path", "Manifest de controle"],
                ["status.storage_dir", "Pasta de versões baixadas"],
              ].map(([chave, label]) => (
                <div className="field" key={chave}>
                  <label className="field-label">{label}</label>
                  <input
                    className="field-input"
                    value={String(form[chave] ?? "")}
                    onChange={(e) => setCampo(chave, e.target.value)}
                  />
                </div>
              ))}
            </>
          )}
        </section>
      </form>
    </div>
  );
}
