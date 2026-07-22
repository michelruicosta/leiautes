import { useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  DIAS_SEMANA_PT,
  MESES_PT,
  brToIso,
  dataLocalIso,
  isoHoje,
  isoToBr,
  mascararDataBr,
  parseIso,
} from "../lib/datas";

type Props = {
  id?: string;
  label: string;
  value: string;
  onChange: (iso: string) => void;
};

type PosicaoPopup = {
  top: number;
  left: number;
};

const LARGURA_POPUP = 280;
const ALTURA_ESTIMADA = 340;

function diasNoMes(ano: number, mes: number): number {
  return new Date(ano, mes + 1, 0).getDate();
}

function calcularPosicao(ancora: DOMRect): PosicaoPopup {
  const margem = 8;
  let top = ancora.bottom + 6;
  let left = ancora.left;

  if (top + ALTURA_ESTIMADA > window.innerHeight - margem) {
    top = Math.max(margem, ancora.top - ALTURA_ESTIMADA - 6);
  }
  if (left + LARGURA_POPUP > window.innerWidth - margem) {
    left = Math.max(margem, window.innerWidth - LARGURA_POPUP - margem);
  }
  if (left < margem) left = margem;

  return { top, left };
}

export default function CampoDataBr({ id, label, value, onChange }: Props) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const wrapRef = useRef<HTMLDivElement>(null);
  const linhaRef = useRef<HTMLDivElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);
  const [texto, setTexto] = useState(() => isoToBr(value));
  const [aberto, setAberto] = useState(false);
  const [posicao, setPosicao] = useState<PosicaoPopup | null>(null);

  const hojeParsed = parseIso(isoHoje());
  const valorParsed = parseIso(value);
  const base = valorParsed ?? hojeParsed ?? { ano: new Date().getFullYear(), mes: new Date().getMonth(), dia: 1 };

  const [anoVisivel, setAnoVisivel] = useState(base.ano);
  const [mesVisivel, setMesVisivel] = useState(base.mes);

  useEffect(() => {
    setTexto(isoToBr(value));
    const p = parseIso(value);
    if (p) {
      setAnoVisivel(p.ano);
      setMesVisivel(p.mes);
    }
  }, [value]);

  useLayoutEffect(() => {
    if (!aberto) {
      setPosicao(null);
      return;
    }
    const atualizar = () => {
      const el = linhaRef.current;
      if (!el) return;
      setPosicao(calcularPosicao(el.getBoundingClientRect()));
    };
    atualizar();
    window.addEventListener("resize", atualizar);
    window.addEventListener("scroll", atualizar, true);
    return () => {
      window.removeEventListener("resize", atualizar);
      window.removeEventListener("scroll", atualizar, true);
    };
  }, [aberto]);

  useEffect(() => {
    if (!aberto) return;
    const fechar = (e: MouseEvent) => {
      const alvo = e.target as Node;
      if (wrapRef.current?.contains(alvo)) return;
      if (popupRef.current?.contains(alvo)) return;
      setAberto(false);
    };
    document.addEventListener("mousedown", fechar);
    return () => document.removeEventListener("mousedown", fechar);
  }, [aberto]);

  const grade = useMemo(() => {
    const total = diasNoMes(anoVisivel, mesVisivel);
    const inicio = new Date(anoVisivel, mesVisivel, 1).getDay();
    const celulas: (number | null)[] = [];
    for (let i = 0; i < inicio; i += 1) celulas.push(null);
    for (let d = 1; d <= total; d += 1) celulas.push(d);
    while (celulas.length % 7 !== 0) celulas.push(null);
    return celulas;
  }, [anoVisivel, mesVisivel]);

  const aplicarTexto = () => {
    const iso = brToIso(texto);
    if (iso) onChange(iso);
    else if (!texto.trim()) onChange("");
  };

  const selecionarDia = (dia: number) => {
    const iso = dataLocalIso(new Date(anoVisivel, mesVisivel, dia));
    onChange(iso);
    setAberto(false);
  };

  const mesAnterior = () => {
    if (mesVisivel === 0) {
      setMesVisivel(11);
      setAnoVisivel((a) => a - 1);
    } else {
      setMesVisivel((m) => m - 1);
    }
  };

  const mesSeguinte = () => {
    if (mesVisivel === 11) {
      setMesVisivel(0);
      setAnoVisivel((a) => a + 1);
    } else {
      setMesVisivel((m) => m + 1);
    }
  };

  const diaSelecionado =
    valorParsed &&
    valorParsed.ano === anoVisivel &&
    valorParsed.mes === mesVisivel
      ? valorParsed.dia
      : null;

  const diaHoje =
    hojeParsed &&
    hojeParsed.ano === anoVisivel &&
    hojeParsed.mes === mesVisivel
      ? hojeParsed.dia
      : null;

  const popup =
    aberto &&
    posicao &&
    createPortal(
      <div
        ref={popupRef}
        className="calendario-popup"
        role="dialog"
        aria-label={`Calendário — ${label}`}
        style={{ top: posicao.top, left: posicao.left }}
      >
        <div className="calendario-cabecalho">
          <button type="button" className="calendario-nav" onClick={mesAnterior} aria-label="Mês anterior">
            ‹
          </button>
          <span className="calendario-titulo">
            {MESES_PT[mesVisivel]} {anoVisivel}
          </span>
          <button type="button" className="calendario-nav" onClick={mesSeguinte} aria-label="Próximo mês">
            ›
          </button>
        </div>

        <div className="calendario-grade-head">
          {DIAS_SEMANA_PT.map((d) => (
            <span key={d} className="calendario-dia-semana">
              {d}
            </span>
          ))}
        </div>

        <div className="calendario-grade">
          {grade.map((dia, idx) =>
            dia === null ? (
              <span key={`v-${idx}`} className="calendario-celula calendario-celula-vazia" />
            ) : (
              <button
                key={`d-${dia}`}
                type="button"
                className={[
                  "calendario-celula",
                  "calendario-dia",
                  diaSelecionado === dia ? "calendario-dia-selecionado" : "",
                  diaHoje === dia ? "calendario-dia-hoje" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => selecionarDia(dia)}
              >
                {dia}
              </button>
            ),
          )}
        </div>

        <div className="calendario-rodape">
          <button
            type="button"
            className="calendario-acao"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => {
              setTexto("");
              onChange("");
              setAberto(false);
            }}
          >
            Limpar
          </button>
          <button
            type="button"
            className="calendario-acao calendario-acao-primaria"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => {
              const hoje = isoHoje();
              onChange(hoje);
              setAberto(false);
            }}
          >
            Hoje
          </button>
        </div>
      </div>,
      document.body,
    );

  return (
    <div className="campo-data-br" ref={wrapRef}>
      <label className="field-label" htmlFor={inputId}>
        {label}
      </label>
      <div className="campo-data-br-linha" ref={linhaRef}>
        <input
          id={inputId}
          className="field-input campo-data-br-input"
          inputMode="numeric"
          placeholder="dd/mm/aaaa"
          maxLength={10}
          autoComplete="off"
          value={texto}
          onChange={(e) => setTexto(mascararDataBr(e.target.value))}
          onBlur={aplicarTexto}
          onKeyDown={(e) => {
            if (e.key === "Enter") aplicarTexto();
          }}
        />
        <button
          type="button"
          className="campo-data-br-btn"
          aria-label={`Abrir calendário — ${label}`}
          aria-expanded={aberto}
          onClick={() => setAberto((v) => !v)}
        >
          <span aria-hidden>📅</span>
        </button>
      </div>
      {popup}
    </div>
  );
}
