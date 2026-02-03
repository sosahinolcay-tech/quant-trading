/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "Geist", "SF Pro Display", "system-ui", "sans-serif"],
      },
      colors: {
        background: "rgb(var(--color-bg) / <alpha-value>)",
        panel: "rgb(var(--color-panel) / <alpha-value>)",
        card: "rgb(var(--color-card) / <alpha-value>)",
        border: "rgb(var(--color-border) / <alpha-value>)",
        accent: "rgb(var(--color-accent) / <alpha-value>)",
        accent2: "rgb(var(--color-accent2) / <alpha-value>)",
        text: "rgb(var(--color-text) / <alpha-value>)",
        muted: "rgb(var(--color-muted) / <alpha-value>)",
      },
      boxShadow: {
        soft: "0 12px 40px rgba(10, 14, 26, 0.3)",
        glass: "0 0 0 1px rgba(255,255,255,0.08), 0 18px 50px rgba(7, 9, 16, 0.6)",
      },
      borderRadius: {
        xl: "12px",
      },
    },
  },
  plugins: [],
};
