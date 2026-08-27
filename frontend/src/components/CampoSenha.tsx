import { useState, type InputHTMLAttributes } from "react";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "onChange"> & {
  label: string;
  onChange: (valor: string) => void;
};

export default function CampoSenha({ id, label, value, onChange, ...rest }: Props) {
  const [visivel, setVisivel] = useState(false);

  return (
    <div className="field">
      <label className="field-label" htmlFor={id}>
        {label}
      </label>
      <div className="campo-senha-wrap">
        <input
          id={id}
          className="field-input"
          type={visivel ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          {...rest}
        />
        <button
          type="button"
          className="campo-senha-toggle"
          onClick={() => setVisivel((atual) => !atual)}
          aria-label={visivel ? "Ocultar senha" : "Mostrar senha"}
          aria-pressed={visivel}
          title={visivel ? "Ocultar senha" : "Mostrar senha"}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
              d={
                visivel
                  ? "M3 3l18 18M10.6 10.6a2 2 0 0 0 2.8 2.8M9.9 5.2A9.8 9.8 0 0 1 12 5c5 0 8.5 4 9.5 7a10.7 10.7 0 0 1-2.2 3.5M6.7 6.7A10.8 10.8 0 0 0 2.5 12c1 3 4.5 7 9.5 7 1.5 0 2.9-.4 4.1-1"
                  : "M2.5 12c1-3 4.5-7 9.5-7s8.5 4 9.5 7c-1 3-4.5 7-9.5 7s-8.5-4-9.5-7Z M12 9a3 3 0 1 1 0 6 3 3 0 0 1 0-6Z"
              }
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
