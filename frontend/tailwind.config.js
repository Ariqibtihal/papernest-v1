/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '"Inter Variable"',
          '"Inter"',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'sans-serif',
        ],
        display: ['"Open Runde"', '"Inter"', 'sans-serif'],
        mono: ['"SFMono-Regular"', 'Consolas', '"Liberation Mono"', 'monospace'],
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        link: "hsl(var(--link))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
          soft: "hsl(var(--primary-soft))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Journal quartile palette (semantic, dipakai langsung tanpa /<alpha>)
        q1: "hsl(var(--q1))",
        q2: "hsl(var(--q2))",
        q3: "hsl(var(--q3))",
        q4: "hsl(var(--q4))",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        pill: "9999px",
      },
      boxShadow: {
        card: "0 1.6px 1.6px hsl(207 80% 43% / 0.04), 0 7px 7px hsl(207 80% 43% / 0.1)",
        elevated:
          "0 4px 8px hsl(207 80% 43% / 0.06), 0 12px 24px hsl(207 80% 43% / 0.14)",
      },
      keyframes: {
        // Floating animations — base rotation diambil dari --paper-rot
        // (default 0deg). Animasi menambahkan delta rotasi & translateY.
        "float-left": {
          "0%, 100%": { transform: "translateY(0) rotate(calc(var(--paper-rot, 0deg) + 0deg))" },
          "50%": { transform: "translateY(-10px) rotate(calc(var(--paper-rot, 0deg) - 2deg))" },
        },
        "float-right": {
          "0%, 100%": { transform: "translateY(0) rotate(calc(var(--paper-rot, 0deg) + 0deg))" },
          "50%": { transform: "translateY(-12px) rotate(calc(var(--paper-rot, 0deg) + 2deg))" },
        },
        "chip-float": {
          "0%, 100%": { transform: "translateY(0)", opacity: "0.9" },
          "50%": { transform: "translateY(-4px)", opacity: "1" },
        },
        // Scanner beam sweep — fades in and out as it scans
        "scan-beam": {
          "0%, 100%": { opacity: "0", transform: "translateY(-22px)" },
          "20%, 80%": { opacity: "1" },
          "50%": { transform: "translateY(22px)" },
        },
        // Subtle vertical floating for browser window mockup
        "window-float": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6px)" },
        },
        // Partikel hero — naik perlahan dari posisi awal lalu reset
        "particle-rise": {
          "0%": { transform: "translateY(8px) translateX(0)" },
          "50%": { transform: "translateY(-40px) translateX(6px)" },
          "100%": { transform: "translateY(-80px) translateX(0)" },
        },
        // Partikel hero — kelap-kelip opacity halus.
        // Peak opacity di-set per partikel via --tw-particle-peak.
        "particle-twinkle": {
          "0%, 100%": { opacity: "0.25" },
          "50%": { opacity: "var(--tw-particle-peak, 0.85)" },
        },
      },
      animation: {
        "float-left": "float-left 6s ease-in-out infinite",
        "float-right": "float-right 7s ease-in-out infinite",
        "chip-float": "chip-float 4s ease-in-out infinite",
        "scan-beam": "scan-beam 3.2s ease-in-out infinite",
        "window-float": "window-float 8s ease-in-out infinite",
        // Gabungan: rise (pergerakan) + twinkle (opacity).
        // Durasi/delay default; di-override per partikel via inline style.
        particle:
          "particle-rise 16s ease-in-out infinite, particle-twinkle 3.2s ease-in-out infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
