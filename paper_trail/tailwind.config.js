/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
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
    },
  },
  plugins: [],
}

