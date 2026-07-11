/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Graphite console — cooler and lighter than the generic near-black+neon
        // pattern. Two semantic accents (not one decorative one): amber reads
        // risk/attention, teal reads healthy/resolved. Every accent use in this
        // product maps to a real severity or status, never decoration alone.
        graphite: {
          950: "#0B0E13",
          900: "#12161E",
          800: "#1A2029",
          700: "#242B37",
          600: "#333C4B",
          500: "#4A5568",
        },
        ink: {
          100: "#EDEFF3",
          300: "#B8C0CE",
          500: "#7C8598",
        },
        signal: {
          DEFAULT: "#FF8552",
          dim: "#7A4530",
        },
        calm: {
          DEFAULT: "#4FD1C5",
          dim: "#2A5C57",
        },
        severity: {
          low: "#5B8DEF",
          medium: "#F2C94C",
          high: "#FF8552",
          critical: "#F45B69",
        },
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
      borderRadius: {
        DEFAULT: "6px",
      },
    },
  },
  plugins: [],
};
