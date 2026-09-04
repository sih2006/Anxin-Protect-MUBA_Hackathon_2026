import type { Config } from "tailwindcss";

/**
 * UI-01: design tokens. Kept intentionally small and semantic (not raw hex
 * everywhere) so typography/colour/spacing/state stay consistent across the
 * app, and so warnings never rely on colour alone (UI-07: every risk colour
 * below is always paired with an icon + text label in components/RiskBadge).
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  darkMode: "media",
  theme: {
    extend: {
      colors: {
        anxin: {
          bg: "#f7f7f5",
          surface: "#ffffff",
          ink: "#1c1c1e",
          "ink-muted": "#5b5b60",
          border: "#e2e2e0",
          brand: "#1f5f5b",
          "brand-dark": "#153f3d",
          "brand-soft": "#e6f0ef",
          risk: {
            low: "#1a7a43",
            "low-bg": "#e8f6ee",
            medium: "#a15c00",
            "medium-bg": "#fdf1e0",
            high: "#b3261e",
            "high-bg": "#fbe9e8",
            unknown: "#4a4a4d",
            "unknown-bg": "#eeeeec",
          },
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "PingFang SC",
          "Noto Sans SC",
          "Microsoft YaHei",
          "system-ui",
          "sans-serif",
        ],
      },
      borderRadius: {
        xl2: "1.25rem",
      },
    },
  },
  plugins: [],
};

export default config;
