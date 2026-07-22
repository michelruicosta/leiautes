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

const ITENS = [
  ["tamanho", "Mínimo de 8 caracteres"],
  ["maiuscula", "Uma letra maiúscula"],
  ["minuscula", "Uma letra minúscula"],
  ["numero", "Um número"],
  ["especial", "Um caractere especial (!@#$%…)"],
] as const;

type Props = {
  senha: string;
};

export default function RequisitosSenha({ senha }: Props) {
  const reqs = avaliarRequisitosSenha(senha);
  return (
    <ul className="requisitos-senha" aria-live="polite">
      {ITENS.map(([chave, label]) => (
        <li key={chave} className={reqs[chave] ? "ok" : undefined}>
          {label}
        </li>
      ))}
    </ul>
  );
}
