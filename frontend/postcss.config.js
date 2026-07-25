// Tailwind v4 prefiksuje samodzielnie (Lightning CSS) — autoprefixer i postcss-import
// są zbędne i usuwane zgodnie z upgrade-guide v4.
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
}
