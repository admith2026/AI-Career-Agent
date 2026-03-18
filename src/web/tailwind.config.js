/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#0F172A',
          900: '#1E293B',
          800: '#1E3A5F',
          700: '#334155',
          600: '#475569',
        },
        cyan: {
          400: '#22D3EE',
          500: '#06B6D4',
          600: '#0891B2',
        },
        gold: {
          400: '#FACC15',
          500: '#EAB308',
        },
        surface: {
          DEFAULT: '#1E293B',
          light: '#334155',
          dark: '#0F172A',
        },
      },
      boxShadow: {
        glow: '0 0 20px rgba(34, 211, 238, 0.15)',
        'glow-gold': '0 0 20px rgba(250, 204, 21, 0.15)',
        card: '0 4px 24px rgba(0, 0, 0, 0.25)',
        'card-hover': '0 8px 32px rgba(0, 0, 0, 0.35)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
        'count-up': 'countUp 0.6s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(-12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 8px rgba(34, 211, 238, 0.2)' },
          '50%': { boxShadow: '0 0 20px rgba(34, 211, 238, 0.4)' },
        },
        countUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
    },
  },
  plugins: [],
};
