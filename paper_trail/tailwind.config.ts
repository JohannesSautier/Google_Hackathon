import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Professional pastel color palette
        primary: {
          50: 'rgb(240, 249, 255)',
          100: 'rgb(224, 242, 254)',
          200: 'rgb(186, 230, 253)',
          300: 'rgb(56, 189, 248)',
          400: 'rgb(56, 189, 248)',
          500: 'rgb(14, 165, 233)',
          600: 'rgb(2, 132, 199)',
          700: 'rgb(3, 105, 161)',
        },
        neutral: {
          50: 'rgb(249, 250, 251)',
          100: 'rgb(243, 244, 246)',
          200: 'rgb(229, 231, 235)',
          300: 'rgb(209, 213, 219)',
          400: 'rgb(156, 163, 175)',
          500: 'rgb(107, 114, 128)',
          600: 'rgb(75, 85, 99)',
          900: 'rgb(17, 24, 39)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Cal Sans', 'Inter', 'sans-serif'],
      },
      animation: {
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-down': 'slideDown 0.5s ease-out',
        'fade-in': 'fadeIn 0.5s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
        'typewriter': 'typewriter 2s steps(40) infinite',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
      },
      keyframes: {
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.9)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
