/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#07090e',
        surface: '#0b0f17',
        'surface-card': '#111723',
        'surface-border': '#1c2436',
        graphite: {
          950: '#06080d',
          900: '#0a0d14',
          850: '#0e121c',
          800: '#131824',
          750: '#171f2f',
          700: '#1d263a',
          600: '#27344e',
          500: '#384869',
        },
        steel: {
          900: '#0e1724',
          800: '#162337',
          700: '#1f304a',
          600: '#2d4366',
          500: '#3e5b87',
          400: '#587caa',
          300: '#7c9ecd',
          200: '#abc2e4',
          100: '#d7e3f4',
        },
        mist: {
          900: '#151d28',
          800: '#232d3d',
          700: '#364357',
          600: '#506078',
          500: '#72839e',
          400: '#9cb0cb',
          300: '#c5d3e6',
          200: '#e1e9f4',
          100: '#f1f5fa',
        },
        icy: {
          500: '#0284c7',
          400: '#0ea5e9',
          300: '#38bdf8',
          200: '#7dd3fc',
          100: '#bae6fd',
        },
        primary: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#b9e0fe',
          300: '#7cc8fd',
          400: '#38bdf8',
          500: '#0284c7',
          600: '#0369a1',
          700: '#075985',
          800: '#0c4a6e',
          900: '#082f49',
        },
        accent: {
          cyan: '#38bdf8',
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#f43f5e',
        }
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.45), inset 0 1px 0 0 rgba(255, 255, 255, 0.05)',
        'glass-hover': '0 12px 40px 0 rgba(0, 0, 0, 0.6), inset 0 1px 0 0 rgba(255, 255, 255, 0.1)',
        'glow-cyan': '0 0 24px -4px rgba(56, 189, 248, 0.25)',
        'glow-emerald': '0 0 24px -4px rgba(16, 185, 129, 0.25)',
        'glow-amber': '0 0 24px -4px rgba(245, 158, 11, 0.25)',
        'inner-glow': 'inset 0 1px 1px 0 rgba(255, 255, 255, 0.08)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'ambient-slow': 'driftSlow 45s ease-in-out infinite alternate',
        'ambient-reverse': 'driftReverse 38s ease-in-out infinite alternate',
        'contour-glow': 'contourGlow 10s ease-in-out infinite alternate',
        'pulse-subtle': 'pulseSubtle 3s ease-in-out infinite',
        'shimmer-ridge': 'shimmerRidge 24s linear infinite',
        'shimmer-ridge-reverse': 'shimmerRidgeReverse 28s linear infinite',
      },
      keyframes: {
        driftSlow: {
          '0%': { transform: 'translate(0, 0) scale(1)' },
          '50%': { transform: 'translate(4%, -3%) scale(1.05)' },
          '100%': { transform: 'translate(-3%, 4%) scale(0.98)' },
        },
        driftReverse: {
          '0%': { transform: 'translate(0, 0) scale(1.02)' },
          '50%': { transform: 'translate(-4%, 5%) scale(0.96)' },
          '100%': { transform: 'translate(3%, -3%) scale(1.04)' },
        },
        contourGlow: {
          '0%, 100%': { opacity: '0.22' },
          '50%': { opacity: '0.38' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%': { opacity: '0.75', transform: 'scale(1.03)' },
        },
        shimmerRidge: {
          '0%': { strokeDashoffset: '1380' },
          '100%': { strokeDashoffset: '0' },
        },
        shimmerRidgeReverse: {
          '0%': { strokeDashoffset: '0' },
          '100%': { strokeDashoffset: '1140' },
        },
      },
    },
  },
  plugins: [],
}


