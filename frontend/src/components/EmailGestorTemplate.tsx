import type { AlteracaoResumo } from "../api/types";

const BLUE = "#2e3192";
const MAX_DIFFS = 5;

type Evidencia = {
  local: string;
  antes?: string;
  depois?: string;
};

function limparAspas(valor: string): string {
  return valor.replace(/^["']|["']$/g, "");
}

function parseEvidencia(texto: string): Evidencia {
  const xsd = texto.match(
    /^(.*?): (linha anterior.*?); antes \((.*)\); depois \((.*)\)$/,
  );
  if (xsd) {
    return { local: `${xsd[1]} · ${xsd[2]}`, antes: xsd[3], depois: xsd[4] };
  }
  const aspas = texto.match(/^(.*?): antes "([\s\S]*)"; depois "([\s\S]*)"$/);
  if (aspas) return { local: aspas[1], antes: aspas[2], depois: aspas[3] };
  const simples = texto.match(/^(.*?): antes '([\s\S]*)'; depois '([\s\S]*)'$/);
  if (simples) {
    return {
      local: simples[1],
      antes: simples[2],
      depois: limparAspas(simples[3]),
    };
  }
  const semAspas = texto.match(/^(.*?): antes ([\s\S]*); depois ([\s\S]*)$/);
  if (semAspas) {
    return { local: semAspas[1], antes: semAspas[2], depois: semAspas[3] };
  }
  const incluido = texto.match(/^(.*?): incluído "([\s\S]*)"$/);
  if (incluido) return { local: incluido[1], depois: incluido[2] };
  const removido = texto.match(/^(.*?): removido "([\s\S]*)"$/);
  if (removido) return { local: removido[1], antes: removido[2] };
  return { local: "Item", depois: texto };
}

function ehNovoArquivo(texto: string): boolean {
  const t = (texto || "").toLowerCase();
  return t.includes("novo arquivo") || t.includes("arquivo novo");
}

function ehEvidenciaTecnica(texto: string): boolean {
  if (ehNovoArquivo(texto)) return false;
  const t = (texto || "").toLowerCase();
  return [
    "etag",
    "last_modified",
    "content_length",
    "final_url",
    "partial_fp",
    "metadados",
    "versão anterior não arquivada",
    "versao anterior nao arquivada",
    "alteracao detectada por metadados",
    "alteração detectada por metadados",
  ].some((k) => t.includes(k));
}

function separarItens(itens: string[]): { tecnicos: string[]; conteudo: string[] } {
  const tecnicos: string[] = [];
  const conteudo: string[] = [];
  for (const bruto of itens || []) {
    if (ehEvidenciaTecnica(bruto)) tecnicos.push(bruto);
    else conteudo.push(bruto);
  }
  return { tecnicos, conteudo };
}

export function alteracaoSoTecnica(alt: AlteracaoResumo): boolean {
  const textos = [
    alt.resumo_executivo || "",
    ...(alt.itens_incluidos || []),
    ...(alt.itens_removidos || []),
    ...(alt.itens_alterados || []),
  ];
  if (textos.some((t) => ehNovoArquivo(t))) return false;

  const { conteudo } = separarItens(alt.itens_alterados || []);
  if (
    (alt.itens_incluidos || []).length ||
    (alt.itens_removidos || []).length ||
    conteudo.length
  ) {
    return false;
  }
  const resumo = (alt.resumo_executivo || "").toLowerCase();
  if (ehEvidenciaTecnica(alt.resumo_executivo || "")) return true;
  if (resumo.includes("nenhuma diferença") || resumo.includes("nenhuma diferenca")) {
    return true;
  }
  return !(
    (alt.itens_incluidos || []).length ||
    (alt.itens_removidos || []).length ||
    (alt.itens_alterados || []).length
  );
}

function contagemCurta(alt: AlteracaoResumo): string {
  if (alteracaoSoTecnica(alt)) return "técnico";
  const { conteudo } = separarItens(alt.itens_alterados || []);
  const nIn = (alt.itens_incluidos || []).length;
  const nOut = (alt.itens_removidos || []).length;
  const nCh = conteudo.length;
  const partes: string[] = [];
  if (nCh) partes.push(`${nCh} mudou`);
  if (nIn) partes.push(`${nIn} entrou`);
  if (nOut) partes.push(`${nOut} saiu`);
  return partes.length ? partes.join(" · ") : "conteúdo alterado";
}

function ListaSimples({
  titulo,
  itens,
  tipo,
}: {
  titulo: string;
  itens: string[];
  tipo: "incluido" | "removido";
}) {
  if (!itens.length) return null;
  const visiveis = itens.slice(0, MAX_DIFFS);
  return (
    <div>
      <p className="email-tpl-sec-label">{titulo}</p>
      <ul className="email-tpl-list">
        {visiveis.map((texto, i) => {
          const ev = parseEvidencia(texto);
          const trecho =
            tipo === "removido"
              ? ev.antes || ev.depois || texto
              : ev.depois || ev.antes || texto;
          return (
            <li key={`${titulo}-${i}`}>
              <strong>{ev.local}:</strong> {trecho}
            </li>
          );
        })}
      </ul>
      {itens.length > MAX_DIFFS ? (
        <p className="email-tpl-more">
          + {itens.length - MAX_DIFFS} item(ns) adicional(is).
        </p>
      ) : null}
    </div>
  );
}

function TabelaMudancas({ itens }: { itens: string[] }) {
  if (!itens.length) return null;
  const visiveis = itens.slice(0, MAX_DIFFS);
  return (
    <div>
      <p className="email-tpl-sec-label">Mudou</p>
      <table className="email-tpl-diff">
        <thead>
          <tr>
            <th>Onde</th>
            <th>Antes</th>
            <th>Depois</th>
          </tr>
        </thead>
        <tbody>
          {visiveis.map((texto, i) => {
            const ev = parseEvidencia(texto);
            return (
              <tr key={`mudou-${i}`}>
                <td className="email-tpl-local">{ev.local}</td>
                <td>{ev.antes || "—"}</td>
                <td>{ev.depois || "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {itens.length > MAX_DIFFS ? (
        <p className="email-tpl-more">
          + {itens.length - MAX_DIFFS} alteração(ões) adicional(is).
        </p>
      ) : null}
    </div>
  );
}

function ArquivoConteudo({ alt }: { alt: AlteracaoResumo }) {
  const { conteudo } = separarItens(alt.itens_alterados || []);
  const rotulo = alt.leiaute_codigo
    ? `${alt.leiaute_codigo} · ${alt.arquivo_nome}`
    : alt.arquivo_nome;
  return (
    <div className="email-tpl-file">
      <p className="email-tpl-file-title">
        <span style={{ color: BLUE }}>{rotulo}</span>
        <span className="email-tpl-muted"> — {contagemCurta(alt)}</span>
      </p>
      <ListaSimples titulo="Entrou" itens={alt.itens_incluidos || []} tipo="incluido" />
      <TabelaMudancas itens={conteudo} />
      <ListaSimples titulo="Saiu" itens={alt.itens_removidos || []} tipo="removido" />
    </div>
  );
}

type Props = {
  dataRef: string;
  alteracoes: AlteracaoResumo[];
};

export default function EmailGestorTemplate({ dataRef, alteracoes }: Props) {
  const precisaAgir = alteracoes.filter((a) => !alteracaoSoTecnica(a));
  const naoPrecisa = alteracoes.filter((a) => alteracaoSoTecnica(a));
  const n = alteracoes.length;

  if (!n) {
    return (
      <div className="email-tpl">
        <div className="email-tpl-marca">
          <img
            className="email-tpl-logo"
            src="/FINAUD_TEC_LOG.jpg"
            alt="FINAUD TEC"
          />
        </div>
        <p className="email-tpl-sem-novidade">
          <strong>
            Nenhum documento novo ou alterado foi identificado na página de leiautes em{" "}
            {dataRef}
          </strong>
          .
        </p>
        <p className="email-tpl-rodape">
          Este e-mail foi gerado automaticamente pelo sistema de monitoramento{" "}
          <b>FINAUD TEC SOLUÇÕES EM TECNOLOGIA</b>.
        </p>
      </div>
    );
  }

  return (
    <div className="email-tpl">
      <div className="email-tpl-marca">
        <img
          className="email-tpl-logo"
          src="/FINAUD_TEC_LOG.jpg"
          alt="FINAUD TEC"
        />
      </div>
      <p className="email-tpl-titulo">
        Atualizações nos leiautes do Bacen em <strong>{dataRef}</strong>.
      </p>
      <p className="email-tpl-lead">
        <strong>{n} arquivo(s)</strong>
        <span className="email-tpl-muted">
          {" "}
          — {precisaAgir.length} precisa agir, {naoPrecisa.length} técnico
        </span>
      </p>

      {precisaAgir.length > 0 ? (
        <section className="email-tpl-bloco">
          <h2 className="email-tpl-h-acao">1. Precisa agir ({precisaAgir.length})</h2>
          <p className="email-tpl-desc">
            Arquivo novo ou mudança de conteúdo — revise o anexo e o Antes/Depois quando
            houver.
          </p>
          {precisaAgir.map((alt) => (
            <ArquivoConteudo key={alt.id} alt={alt} />
          ))}
        </section>
      ) : null}

      {naoPrecisa.length > 0 ? (
        <section className="email-tpl-bloco">
          <h2 className="email-tpl-h-tech">2. Não precisa agir ({naoPrecisa.length})</h2>
          <p className="email-tpl-desc">
            Só republicação no site do Bacen (data/tamanho/identificador). Sem mudança
            de texto, célula ou tabela.
          </p>
          <ul className="email-tpl-tech-list">
            {naoPrecisa.map((alt) => {
              const rotulo = alt.leiaute_codigo
                ? `${alt.leiaute_codigo} · ${alt.arquivo_nome}`
                : alt.arquivo_nome;
              return <li key={alt.id}>{rotulo}</li>;
            })}
          </ul>
        </section>
      ) : null}

      <p className="email-tpl-rodape">
        E-mail automático — FINAUD TEC SOLUÇÕES EM TECNOLOGIA
      </p>
    </div>
  );
}
