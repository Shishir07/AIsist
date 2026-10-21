/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f5f3ff',
          100: '#ede9fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
        },
        surface: {
          DEFAULT: 'rgba(255,255,255,0.04)',
          md: 'rgba(255,255,255,0.07)',
          lg: 'rgba(255,255,255,0.10)',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'user-bubble': 'linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)',
      },
      boxShadow: {
        'glow-sm': '0 0 20px rgba(139,92,246,0.25)',
        'glow':    '0 0 40px rgba(139,92,246,0.35)',
        'glow-lg': '0 0 60px rgba(139,92,246,0.5)',
        'glass':   '0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08)',
      },
      backdropBlur: {
        xs: '4px',
      },
      animation: {
        'ping-slow':  'ping 2s cubic-bezier(0,0,0.2,1) infinite',
        'ping-slow2': 'ping 2s cubic-bezier(0,0,0.2,1) infinite 0.4s',
        'ping-slow3': 'ping 2s cubic-bezier(0,0,0.2,1) infinite 0.8s',
        'float':      'float 6s ease-in-out infinite',
        'gradient':   'gradientShift 8s ease infinite',
        'slide-up':   'slideUp 0.3s ease-out',
        'fade-in':    'fadeIn 0.4s ease-out',
        'scale-in':   'scaleIn 0.2s ease-out',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%':      { transform: 'translateY(-8px)' },
        },
        gradientShift: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%':      { backgroundPosition: '100% 50%' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        scaleIn: {
          from: { opacity: '0', transform: 'scale(0.9)' },
          to:   { opacity: '1', transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
}
