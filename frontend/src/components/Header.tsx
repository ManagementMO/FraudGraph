"use client";

import { useTheme, type Theme } from "./ThemeProvider";

const THEMES: { value: Theme; label: string }[] = [
  { value: "dark", label: "Dark" },
  { value: "light", label: "Light" },
  { value: "cyberpunk", label: "Cyber" },
];

export function Header() {
  const { theme, setTheme } = useTheme();

  return (
    <header className="flex items-center justify-between py-2 px-4 bg-bg-secondary border-b border-border">
      <span className="font-mono text-lg font-bold text-text-primary tracking-tight">
        FraudGraph
      </span>
      <div className="flex items-center gap-1">
        {THEMES.map((t) => (
          <button
            key={t.value}
            onClick={() => setTheme(t.value)}
            className={`px-2.5 py-1 text-xs rounded-md transition-colors ${
              theme === t.value
                ? "bg-accent text-bg-primary font-semibold"
                : "text-text-secondary hover:text-text-primary hover:bg-bg-primary"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
    </header>
  );
}
