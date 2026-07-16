/**
 * Interop CJS/ESM dla react-plotly.js (review 2026-07-16).
 *
 * Vite 8 (rolldown) potrafi opakować default CJS-owego modułu jako
 * { default: Component } — bezpośredni `import Plot from 'react-plotly.js'`
 * dawał wtedy obiekt zamiast komponentu i wywalał cały render Reacta
 * ("Element type is invalid" w PortfolioNode → pusty <div id="root">).
 * Wrapper obsługuje oba kształty modułu, więc działa w dev, build i vitest.
 */
import PlotImport from 'react-plotly.js'

type PlotComponent = typeof PlotImport

const candidate = PlotImport as unknown as { default?: PlotComponent }
const Plot: PlotComponent = (candidate.default ?? PlotImport) as PlotComponent

export default Plot
