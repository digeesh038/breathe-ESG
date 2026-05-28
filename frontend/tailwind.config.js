/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          900: "#0a2a20",
          800: "#0e3b2e",
          700: "#134c3a",
          accent: "#25a777",
          primary: "#127a55",
        },
        scope1: "#b4600f",
        scope2: "#2563c4",
        scope3: "#6a47c9",
      },
      fontFamily: {
        sans: ['"Inter"', "system-ui", "-apple-system", '"Segoe UI"', "Roboto", "sans-serif"],
      },
      boxShadow: {
        sm: "0 1px 2px rgba(15, 31, 26, 0.05), 0 1px 3px rgba(15, 31, 26, 0.04)",
        md: "0 6px 22px rgba(15, 31, 26, 0.09)",
      },
      borderRadius: {
        DEFAULT: "14px",
        sm: "9px",
        pill: "999px",
      },
    },
  },
  plugins: [],
};
