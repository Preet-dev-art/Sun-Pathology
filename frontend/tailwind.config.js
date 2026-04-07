export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Sun Pathology brand colors
        "sun-blue":   "#1E3A5F",   // primary — dark navy
        "sun-sky":    "#2E86C1",   // accent — medium blue
        "sun-light":  "#EBF5FB",   // background tint
        "sun-orange": "#E67E22",   // CTA / highlights
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      }
    },
  },
  plugins: [],
}