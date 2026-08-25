import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

export type PreferenciaTema = "claro" | "escuro";

const STORAGE_KEY = "leiautes_theme";

type ThemeContextValue = {
  preferencia: PreferenciaTema;
  tema: PreferenciaTema;
  setPreferencia: (p: PreferenciaTema) => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

function lerPreferencia(): PreferenciaTema {
  try {
    const s = localStorage.getItem(STORAGE_KEY);
    if (s === "claro" || s === "escuro") return s;
    // legado "sistema": fixa no tema do Windows na primeira leitura
    if (s === "sistema") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "escuro"
        : "claro";
    }
  } catch {
    /* ignore */
  }
  return "claro";
}

function aplicarNoDocumento(tema: PreferenciaTema) {
  document.documentElement.setAttribute("data-theme", tema);
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preferencia, setPreferenciaState] = useState<PreferenciaTema>(() =>
    typeof window !== "undefined" ? lerPreferencia() : "claro",
  );

  const setPreferencia = (p: PreferenciaTema) => {
    setPreferenciaState(p);
    try {
      localStorage.setItem(STORAGE_KEY, p);
    } catch {
      /* ignore */
    }
    aplicarNoDocumento(p);
  };

  useEffect(() => {
    aplicarNoDocumento(preferencia);
    try {
      localStorage.setItem(STORAGE_KEY, preferencia);
    } catch {
      /* ignore */
    }
  }, [preferencia]);

  return (
    <ThemeContext.Provider
      value={{ preferencia, tema: preferencia, setPreferencia }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme deve ser usado dentro de ThemeProvider");
  }
  return ctx;
}
