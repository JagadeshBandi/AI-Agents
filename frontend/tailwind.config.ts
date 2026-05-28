import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        zinc: {
          50: "#fafafa",
          100: "#f4f4f5",
          200: "#e4e4e7",
          300: "#d4d4d8",
          400: "#a1a1aa",
          500: "#71717a",
          600: "#52525b",
          700: "#3f3f46",
          800: "#27272a",
          900: "#18181b",
          950: "#09090b",
        },
      },
      animation: {
        "console-in": "console-line-in 0.25s ease-out forwards",
        "slide-up": "slide-up 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "glow-pulse": "glow-pulse 2s ease-in-out infinite",
        "fade-in": "fade-in 0.3s ease-out forwards",
        "pulse-ring": "pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 3s linear infinite",
        "bounce-dot": "bounce-dot 1.4s ease-in-out infinite",
      },
      keyframes: {
        "console-line-in": {
          from: { opacity: "0", transform: "translateX(-6px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(16px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "glow-pulse": {
          "0%, 100%": {
            boxShadow: "0 0 8px rgba(99,102,241,0.3), 0 0 20px rgba(99,102,241,0.1)",
          },
          "50%": {
            boxShadow: "0 0 16px rgba(99,102,241,0.6), 0 0 40px rgba(99,102,241,0.2)",
          },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "pulse-ring": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.4" },
        },
        "bounce-dot": {
          "0%, 80%, 100%": { transform: "scale(0.6)", opacity: "0.4" },
          "40%": { transform: "scale(1)", opacity: "1" },
        },
      },
      backgroundImage: {
        "indigo-gradient": "linear-gradient(135deg, #6366f1, #7c3aed)",
        "zinc-gradient": "linear-gradient(135deg, #27272a, #18181b)",
      },
      boxShadow: {
        "glow-indigo": "0 0 20px rgba(99,102,241,0.25)",
        "glow-emerald": "0 0 20px rgba(52,211,153,0.2)",
        "panel": "0 4px 24px rgba(0,0,0,0.4)",
      },
    },
  },
  plugins: [],
};

export default config;
