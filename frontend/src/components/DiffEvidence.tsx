type DiffTipo = "incluido" | "alterado" | "removido";

type Evidencia = {
  local: string;
  antes?: string;
  depois?: string;
  detalhe?: string;
};

type EvidenciaParseada = Evidencia & {
  textoOriginal: string;
};

function limparAspas(valor: string): string {
  return valor.replace(/^["']|["']$/g, "");
}

function parseEvidencia(texto: string, tipo: DiffTipo): Evidencia {
  const xsd = texto.match(/^(.*?): (linha anterior.*?); antes \((.*)\); depois \((.*)\)$/);
  if (xsd) {
    return {
      local: `${xsd[1]} · ${xsd[2]}`,
      antes: xsd[3],
      depois: xsd[4],
    };
  }

  const antesDepoisAspas = texto.match(/^(.*?): antes "([\s\S]*)"; depois "([\s\S]*)"$/);
  if (antesDepoisAspas) {
    return {
      local: antesDepoisAspas[1],
      antes: antesDepoisAspas[2],
      depois: antesDepoisAspas[3],
    };
  }

  const antesDepoisSimples = texto.match(/^(.*?): antes '([\s\S]*)'; depois '([\s\S]*)'$/);
  if (antesDepoisSimples) {
    return {
      local: antesDepoisSimples[1],
      antes: antesDepoisSimples[2],
      depois: limparAspas(antesDepoisSimples[3]),
    };
  }

  const incluidoComLinha = texto.match(/^(.*?): incluído "([\s\S]*)"$/);
  if (incluidoComLinha) {
    return {
      local: incluidoComLinha[1],
      depois: incluidoComLinha[2],
    };
  }

  const removidoComLinha = texto.match(/^(.*?): removido "([\s\S]*)"$/);
  if (removidoComLinha) {
    return {
      local: removidoComLinha[1],
      antes: removidoComLinha[2],
    };
  }

  const zipIncluido = texto.match(/^Arquivo interno incluído: ([^;]+); evidência: "([\s\S]*)"$/);
  if (zipIncluido) {
    return {
      local: `Arquivo interno ${zipIncluido[1]}`,
      depois: zipIncluido[2],
    };
  }

  if (tipo === "incluido") return { local: "Novo item", depois: texto };
  if (tipo === "removido") return { local: "Item removido", antes: texto };
  return { local: "Alteração identificada", detalhe: texto };
}

function tipoLabel(tipo: DiffTipo): string {
  if (tipo === "incluido") return "Entrou";
  if (tipo === "removido") return "Saiu";
  return "Mudou";
}

function vazioLabel(tipo: DiffTipo): string {
  if (tipo === "incluido") return "Nenhuma inclusão identificada.";
  if (tipo === "removido") return "Nenhuma remoção identificada.";
  return "Nenhuma alteração de conteúdo identificada.";
}

function EvidenceCard({ texto, tipo }: { texto: string; tipo: DiffTipo }) {
  const evidencia = parseEvidencia(texto, tipo);
  return (
    <article className={`evidence-card evidence-${tipo}`}>
      <header>
        <span>{tipoLabel(tipo)}</span>
        <strong>{evidencia.local}</strong>
      </header>
      {evidencia.antes || evidencia.depois ? (
        <div className="evidence-before-after">
          {tipo === "alterado" && (
            <div>
              <small>Antes</small>
              <p>{evidencia.antes || "Não existia informação anterior."}</p>
            </div>
          )}
          {tipo === "alterado" && (
            <div>
              <small>Depois</small>
              <p>{evidencia.depois || "Sem novo valor informado."}</p>
            </div>
          )}
          {tipo === "incluido" && (
            <div>
              <p>{evidencia.depois || evidencia.detalhe || texto}</p>
            </div>
          )}
          {tipo === "removido" && (
            <div>
              <p>{evidencia.antes || evidencia.detalhe || texto}</p>
            </div>
          )}
        </div>
      ) : (
        <p className="evidence-raw">{evidencia.detalhe || texto}</p>
      )}
    </article>
  );
}

function grupoLocal(local: string): string {
  const pagina = local.match(/^(Página \d+)/);
  if (pagina) return pagina[1];
  const arquivoInterno = local.match(/^(Arquivo interno [^-:]+)/);
  if (arquivoInterno) return arquivoInterno[1].trim();
  if (/^linha (atual|anterior) \d+/.test(local)) return "Linhas do arquivo";
  return local;
}

function numerosLinha(itens: EvidenciaParseada[], tipo: DiffTipo): string {
  const padrao = tipo === "removido" ? /linha anterior (\d+)/i : /linha atual (\d+)/i;
  const numeros = itens
    .map((item) => item.local.match(padrao)?.[1])
    .filter(Boolean)
    .map(Number)
    .sort((a, b) => a - b);
  if (!numeros.length) return "";
  if (numeros.length === 1) return `linha ${numeros[0]}`;
  return `linhas ${numeros[0]} a ${numeros[numeros.length - 1]}`;
}

function AgrupadoCard({
  grupo,
  itens,
  tipo,
}: {
  grupo: string;
  itens: EvidenciaParseada[];
  tipo: Exclude<DiffTipo, "alterado">;
}) {
  const local = numerosLinha(itens, tipo);
  const textos = itens.map((item) =>
    tipo === "incluido"
      ? item.depois || item.detalhe || item.textoOriginal
      : item.antes || item.detalhe || item.textoOriginal,
  );

  return (
    <article className={`evidence-card evidence-${tipo}`}>
      <header>
        <span>{tipoLabel(tipo)}</span>
        <strong>{local ? `${grupo} · ${local}` : grupo}</strong>
      </header>
      <div className="evidence-single">
        {textos.map((texto, index) => (
          <p key={`${grupo}-${index}`}>{texto}</p>
        ))}
      </div>
    </article>
  );
}

function agruparItens(itens: string[], tipo: DiffTipo) {
  const grupos: Array<{ grupo: string; itens: EvidenciaParseada[] }> = [];
  for (const item of itens) {
    const evidencia = { ...parseEvidencia(item, tipo), textoOriginal: item };
    const grupo = tipo === "alterado" ? item : grupoLocal(evidencia.local);
    const ultimo = grupos[grupos.length - 1];
    if (ultimo && ultimo.grupo === grupo) {
      ultimo.itens.push(evidencia);
    } else {
      grupos.push({ grupo, itens: [evidencia] });
    }
  }
  return grupos;
}

export function DiffEvidenceList({
  titulo,
  tipo,
  itens,
}: {
  titulo: string;
  tipo: DiffTipo;
  itens: string[];
}) {
  return (
    <section className="evidence-section">
      <h3>{titulo}</h3>
      {itens.length ? (
        <div className="evidence-list">
          {tipo === "alterado"
            ? itens.map((item, index) => (
                <EvidenceCard key={`${tipo}-${index}-${item}`} texto={item} tipo={tipo} />
              ))
            : agruparItens(itens, tipo).map((grupo, index) => (
                <AgrupadoCard
                  key={`${tipo}-${index}-${grupo.grupo}`}
                  grupo={grupo.grupo}
                  itens={grupo.itens}
                  tipo={tipo}
                />
              ))}
        </div>
      ) : (
        <p className="meta">{vazioLabel(tipo)}</p>
      )}
    </section>
  );
}
