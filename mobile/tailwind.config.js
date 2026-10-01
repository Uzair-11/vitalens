/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./App.{js,jsx,ts,tsx}", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        deepTeal: {
          DEFAULT: '#0F5C5E',
          50: '#E6EFEF',
          100: '#C0DCDD',
          500: '#0F5C5E',
          600: '#0C4E50',
          700: '#0A4143',
          800: '#073233',
        },
        warmIvory: {
          DEFAULT: '#F7F5EF',
          light: '#FCFBF8',
          dark: '#EFEBE2',
        },
        sage: {
          DEFAULT: '#8BAA9A',
          50: '#EEF4F0',
          100: '#D5E4DB',
          500: '#8BAA9A',
          600: '#759585',
        },
        mutedCoral: {
          DEFAULT: '#D97A6A',
          50: '#FBF0EE',
          100: '#F5DCD7',
          500: '#D97A6A',
          600: '#C86554',
        },
        charcoal: {
          DEFAULT: '#263334',
          50: '#F4F6F6',
          500: '#263334',
          900: '#141B1C',
        },
        slateText: {
          DEFAULT: '#687576',
          muted: '#97A3A4',
        },
        forestGreen: '#43866A',
        ochre: '#C99A45',
        terracotta: '#B84C4C',
      }
    },
  },
  plugins: [],
}
