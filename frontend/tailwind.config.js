/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0B0F1A',
          800: '#0F172A',
          700: '#1E293B',
          600: '#334155',
        },
        accent: {
          500: '#6366F1',
          400: '#818CF8',
          600: '#4F46E5',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
