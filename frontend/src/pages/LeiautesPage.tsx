import { type FormEvent, useEffect, useState } from "react";
import {
  atualizarLeiaute,
  criarLeiaute,
  excluirLeiaute,
  listarLeiautes,
} from "../api/leiautes";
import ModalConfirmacao, { type ConfirmacaoConfig } from "../components/ModalConfirmacao";
import type { LeiautePayload, LeiauteResumo } from "../api/types";

const VAZIO: LeiautePayload = {
  codigo: "",
  nome: "",
  categoria: "",
  url_bacen: "",
  tipos_arquivo: ["pdf", "xls", "xlsx", "xsd", "zip"],
  ativo: true,
};

function listaTexto(valor: string): string[] {
  return valor
    .split(/[\n,;]+/)
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

function textoLista(valor: string[]): string {
  return valor.join(", ");
}

export default function LeiautesPage() {
  const [itens, setItens] = useState<LeiauteResumo[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [modal, setModal] = useState<LeiauteResumo | "novo" | null>(null);
  const [form, setForm] = useState<LeiautePayload>(VAZIO);
  const [validacao, setValidacao] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);
  const [confirmacao, setConfirmacao] = useState<ConfirmacaoConfig | null>(null);

  const carregar = () => {
    listarLeiautes()
      .then((resp) => setItens(resp.leiautes))
      .catch(() => setErro("API indisponível."));
  };

  useEffect(() => {
    carregar();
  }, []);

  const abrirNovo = () => {
    setModal("novo");
    setForm(VAZIO);
    setValidacao(null);
    setErro(null);
    setMsg(null);
  };

  const abrirEdicao = (item: LeiauteResumo) => {
    setModal(item);
    setForm({
      codigo: item.codigo,
      nome: item.nome,
      categoria: item.categoria,
      url_bacen: item.url_bacen,
      tipos_arquivo: item.tipos_arquivo,
      ativo: item.ativo,
    });
    setValidacao(null);
    setErro(null);
    setMsg(null);
  };

  const validar = (): string | null => {
    if (form.codigo.trim().length < 2) return "Informe o código do leiaute.";
    if (form.nome.trim().length < 2) return "Informe o nome do leiaute.";
    if (form.categoria.trim().length < 2) return "Informe a categoria.";
    if (!form.url_bacen.startsWith("http")) return "Informe uma URL Bacen válida.";
    if (form.tipos_arquivo.length === 0) return "Informe ao menos um tipo de arquivo.";
    return null;
  };

  const salvar = async (event: FormEvent) => {
    event.preventDefault();
    const problema = validar();
    if (problema) {
      setValidacao(problema);
      return;
    }

    setSalvando(true);
    setErro(null);
    setMsg(null);
    setValidacao(null);
    try {
      if (modal === "novo") {
        await criarLeiaute(form);
        setMsg("Leiaute criado.");
      } else if (modal) {
        await atualizarLeiaute(modal.id, form);
        setMsg("Leiaute atualizado.");
      }
      setModal(null);
      carregar();
    } catch {
      setErro("Não foi possível salvar o leiaute. Verifique se o código já existe.");
    } finally {
      setSalvando(false);
    }
  };

  const alternarAtivo = (item: LeiauteResumo) => {
    const inativar = item.ativo;
    setConfirmacao({
      titulo: inativar ? "Inativar leiaute" : "Ativar leiaute",
      texto: inativar
        ? `Inativar o leiaute "${item.codigo}"? Ele deixará de ser monitorado até ser reativado.`
        : `Ativar o leiaute "${item.codigo}" para voltar ao monitoramento?`,
      rotuloOk: inativar ? "Inativar" : "Ativar",
      perigo: inativar,
      onCancel: () => setConfirmacao(null),
      onConfirm: async () => {
        await atualizarLeiaute(item.id, {
          codigo: item.codigo,
          nome: item.nome,
          categoria: item.categoria,
          url_bacen: item.url_bacen,
          tipos_arquivo: item.tipos_arquivo,
          ativo: !item.ativo,
        });
        setConfirmacao(null);
        setMsg(inativar ? "Leiaute inativado." : "Leiaute ativado.");
        carregar();
      },
    });
  };

  const excluir = (item: LeiauteResumo) => {
    setConfirmacao({
      titulo: "Excluir leiaute",
      texto: `Excluir permanentemente o leiaute "${item.codigo}"? Esta ação não pode ser desfeita.`,
      rotuloOk: "Excluir",
      exigirDigitacao: "excluir",
      onCancel: () => setConfirmacao(null),
      onConfirm: async () => {
        try {
          await excluirLeiaute(item.id);
          setConfirmacao(null);
          setMsg("Leiaute excluído.");
          carregar();
        } catch (e) {
          setConfirmacao(null);
          setErro(e instanceof Error ? e.message : "Não foi possível excluir o leiaute.");
        }
      },
    });
  };

  return (
    <div className="admin-page">
      <div className="page-cabecalho">
        <div>
          <h1 className="page-title">Cadastro de Leiautes</h1>
          <p className="page-sub">Leiautes do Bacen e tipos de arquivo que o robô acompanha.</p>
        </div>
        <button type="button" className="btn-novo" onClick={abrirNovo}>
          + Novo leiaute
        </button>
      </div>

      {erro && <p className="erro">{erro}</p>}
      {msg && <p className="login-sucesso">{msg}</p>}

      <div className="tabela-wrap">
        <table className="tabela">
          <thead>
            <tr>
              <th>Código</th>
              <th>Nome</th>
              <th>Categoria</th>
              <th>Tipos</th>
              <th>Status</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {itens.map((item) => (
              <tr key={item.id}>
                <td>
                  <strong>{item.codigo}</strong>
                </td>
                <td>{item.nome}</td>
                <td>{item.categoria}</td>
                <td>
                  <div className="tags-inline">
                    {item.tipos_arquivo.map((tipo) => (
                      <span key={tipo} className="tag">
                        {tipo.toUpperCase()}
                      </span>
                    ))}
                  </div>
                </td>
                <td className={item.ativo ? "status-ok" : "status-erro"}>
                  {item.ativo ? "Ativo" : "Inativo"}
                </td>
                <td>
                  <div className="acoes-linha">
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => abrirEdicao(item)}
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => alternarAtivo(item)}
                    >
                      {item.ativo ? "Inativar" : "Ativar"}
                    </button>
                    <button type="button" className="btn-perigo" onClick={() => excluir(item)}>
                      Excluir
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modal && (
        <div className="modal-backdrop" onClick={() => setModal(null)}>
          <form
            className="modal-detalhe modal-form"
            onSubmit={(event) => void salvar(event)}
            onClick={(event) => event.stopPropagation()}
          >
            <header className="modal-detalhe-head">
              <div>
                <h2>{modal === "novo" ? "Novo leiaute" : "Editar leiaute"}</h2>
                <p className="meta">Preencha os dados da página Bacen monitorada.</p>
              </div>
              <button
                type="button"
                className="modal-fechar"
                aria-label="Fechar"
                onClick={() => setModal(null)}
              >
                ×
              </button>
            </header>
            <div className="modal-form-body">
              {validacao && <p className="erro">{validacao}</p>}
              <div className="config-dupla">
                <label className="field">
                  <span className="field-label">Código</span>
                  <input
                    className="field-input"
                    value={form.codigo}
                    onChange={(e) => setForm({ ...form, codigo: e.target.value })}
                  />
                </label>
                <label className="field">
                  <span className="field-label">Categoria</span>
                  <input
                    className="field-input"
                    value={form.categoria}
                    onChange={(e) => setForm({ ...form, categoria: e.target.value })}
                  />
                </label>
              </div>
              <label className="field">
                <span className="field-label">Nome</span>
                <input
                  className="field-input"
                  value={form.nome}
                  onChange={(e) => setForm({ ...form, nome: e.target.value })}
                />
              </label>
              <label className="field">
                <span className="field-label">URL Bacen</span>
                <input
                  className="field-input"
                  value={form.url_bacen}
                  onChange={(e) => setForm({ ...form, url_bacen: e.target.value })}
                />
              </label>
              <label className="field">
                <span className="field-label">Tipos de arquivo</span>
                <input
                  className="field-input"
                  value={textoLista(form.tipos_arquivo)}
                  onChange={(e) =>
                    setForm({ ...form, tipos_arquivo: listaTexto(e.target.value) })
                  }
                />
              </label>
              <label className="admin-dia-chip">
                <input
                  type="checkbox"
                  checked={form.ativo}
                  onChange={(e) => setForm({ ...form, ativo: e.target.checked })}
                />
                Leiaute ativo
              </label>
              <div className="modal-form-acoes">
                <button type="button" className="btn-secondary" onClick={() => setModal(null)}>
                  Cancelar
                </button>
                <button type="submit" className="btn-novo" disabled={salvando}>
                  {salvando ? "Salvando..." : "Salvar leiaute"}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}
      {confirmacao && <ModalConfirmacao aberto {...confirmacao} />}
    </div>
  );
}
