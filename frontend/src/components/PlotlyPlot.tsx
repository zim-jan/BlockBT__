import PlotImport from 'react-plotly.js'

function getComponent(comp: any): any {
  if (comp && comp.default) {
    return getComponent(comp.default)
  }
  return comp
}

export default function Plot(props: any) {
  const PlotComp = getComponent(PlotImport)

  if (!PlotComp || typeof PlotComp !== 'function') {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center text-error border border-error/20 bg-error/5 rounded text-sm p-4 text-center">
        <span>Plotly is not loaded correctly.</span>
        <span className="text-xs mt-1">Type: {typeof PlotComp}</span>
      </div>
    )
  }

  return <PlotComp {...props} />
}
