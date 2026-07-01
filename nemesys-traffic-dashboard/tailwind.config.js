/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        void: '#06080a',
        panel: '#0b0f12',
        panel2: '#0f1418',
        line: '#1c2329',
        signal: '#39ff8f',
        amber: '#ffb648',
        crimson: '#ff4d5e',
        cyan: '#3ad6ff',
        muted: '#5d6b73'
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
        sans: ['"Inter"', 'system-ui', 'sans-serif']
      },
      boxShadow: {
        glow: '0 0 20px -4px rgba(57,255,143,0.35)',
        glowAmber: '0 0 20px -4px rgba(255,182,72,0.35)',
        glowRed: '0 0 20px -4px rgba(255,77,94,0.4)'
      },
      keyframes: {
        scanline: { '0%': { transform: 'translateY(-100%)' }, '100%': { transform: 'translateY(100%)' } },
        pulseDot: { '0%,100%': { opacity: 1 }, '50%': { opacity: 0.3 } }
      },
      animation: {
        scanline: 'scanline 4s linear infinite',
        pulseDot: 'pulseDot 1.6s ease-in-out infinite'
      }
    }
  },
  plugins: []
}
