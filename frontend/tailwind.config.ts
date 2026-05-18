import type { Config } from "tailwindcss";

// Design tokens — Section 8 of the build doc.
// Dark slate sidebar, light content, Indigo primary; Emerald/Amber/Red for
// healthy/warning/critical. Geist for UI, Geist Mono for scores/code.
// Explicitly NOT: purple gradients, Inter font, cookie-cutter SaaS look.
const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sidebar: {
          DEFAULT: "#0f172a", // slate-900
          fg: "#cbd5e1", // slate-300
          active: "#1e293b", // slate-800
        },
        brand: {
          DEFAULT: "#4f46e5", // indigo-600
          hover: "#4338ca", // indigo-700
          fg: "#eef2ff", // indigo-50
        },
        healthy: "#10b981", // emerald-500
        warning: "#f59e0b", // amber-500
        critical: "#ef4444", // red-500
        content: "#ffffff",
        canvas: "#f8fafc", // slate-50 page background
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
