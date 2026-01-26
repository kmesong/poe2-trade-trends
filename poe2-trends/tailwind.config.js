export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        poe: {
          bg: '#0a0a0a',
          card: '#141414',
          border: '#2a2a2a',
          gold: '#c8aa6d',
          golddim: '#8a754c',
          text: '#a38d6d',
          highlight: '#fff4d6',
          red: '#bd3333'
        }
      },
      fontFamily: {
        serif: ['"Cinzel"', 'serif'],
        sans: ['"Inter"', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
