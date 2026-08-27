const RE = {
  maiuscula: /[A-Z]/,
  minuscula: /[a-z]/,
  numero: /\d/,
  especial: /[!@#$%^&*(),.?":{}|<>_\-+=[\]\\;/]/,
};

export function avaliarRequisitosSenha(senha: string) {
  return {
    tamanho: senha.length >= 8,
    maiuscula: RE.maiuscula.test(senha),
    minuscula: RE.minuscula.test(senha),
    numero: RE.numero.test(senha),
    especial: RE.especial.test(senha),
  };
}

export function senhaAtendePolitica(senha: string) {
  return Object.values(avaliarRequisitosSenha(senha)).every(Boolean);
}

export function mensagemSenhaIncompleta(senha: string): string | null {
  const reqs = avaliarRequisitosSenha(senha);
  const faltando: string[] = [];
  if (!reqs.tamanho) faltando.push("mínimo 8 caracteres");
  if (!reqs.maiuscula) faltando.push("letra maiúscula");
  if (!reqs.minuscula) faltando.push("letra minúscula");
  if (!reqs.numero) faltando.push("número");
  if (!reqs.especial) faltando.push("caractere especial");
  if (!faltando.length) return null;
  return "A senha ainda precisa de: " + faltando.join(", ") + ".";
}

const ITENS = [
  ["tamanho", "Mínimo 8 caracteres"],
  ["maiuscula", "Letra maiúscula"],
  ["minuscula", "Letra minúscula"],
  ["numero", "Pelo menos um número"],
  ["especial", "Caractere especial (!@#$…)"],
] as const;

/** Evita mojibake: escapes ASCII no JS, nao depende de encoding do CSS. */
const MARCA_OK = "\u2713";
const MARCA_PENDENTE = "\u25CB";

type Props = {
  senha: string;
  id?: string;
};

export default function RequisitosSenha({ senha, id = "requisitos-senha" }: Props) {
  const reqs = avaliarRequisitosSenha(senha);
  return (
    <ul className="requisitos-senha" id={id} aria-live="polite">
      {ITENS.map(([chave, label]) => {
        const ok = reqs[chave];
        return (
          <li key={chave} className={ok ? "ok" : undefined}>
            <span className="requisitos-senha-marca" aria-hidden>
              {ok ? MARCA_OK : MARCA_PENDENTE}
            </span>
            {label}
          </li>
        );
      })}
    </ul>
  );
}
