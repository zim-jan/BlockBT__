/**
 * OptimizationChart — A lightweight SVG scatter plot to visualize Optuna trials.
 * 
 * Plots Trial Number vs Objective Value.
 */

import type {OptunaTrial} from '../../../types/types'

interface Props {
  trials: OptunaTrial[]
  metricName: string
}

export function OptimizationChart({ trials, metricName }: Props) {
  if (!trials || trials.length === 0) return null

  const width = 280
  const height = 140
  const padding = 30

  // Filter out failed trials
  const validTrials = trials.filter(t => t.value !== null && t.value !== undefined)
  if (validTrials.length === 0) return <div style={{ fontSize: 10, color: '#94a3b8' }}>No valid trials to display.</div>

  const values = validTrials.map(t => t.value as number)
  const minVal = Math.min(...values)
  const maxVal = Math.max(...values)
  const valRange = maxVal - minVal || 1

  const getX = (index: number) => padding + (index / (trials.length - 1)) * (width - 2 * padding)
  const getY = (val: number) => height - padding - ((val - minVal) / valRange) * (height - 2 * padding)

  return (
    <div style={{ marginTop: 10, background: 'rgba(0,0,0,0.3)', borderRadius: 8, padding: 10 }}>
      <div style={{ fontSize: 10, color: '#a78bfa', fontWeight: 600, marginBottom: 6 }}>
        HISTORY: {metricName}
      </div>
      
      <svg width={width} height={height} style={{ overflow: 'visible' }}>
        {/* Axes */}
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#475569" strokeWidth="1" />
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#475569" strokeWidth="1" />

        {/* Labels */}
        <text x={width / 2} y={height - 5} fill="#64748b" fontSize="8" textAnchor="middle">Trial #</text>
        <text x={5} y={height / 2} fill="#64748b" fontSize="8" textAnchor="middle" transform={`rotate(-90, 5, ${height / 2})`}>Value</text>

        {/* Data points */}
        {validTrials.map((t, i) => (
          <circle 
            key={i} 
            cx={getX(t.number)} 
            cy={getY(t.value as number)} 
            r="3" 
            fill={t.value === maxVal ? '#10b981' : '#38bdf8'} 
            opacity="0.7"
          >
            <title>Trial {t.number}: {t.value?.toFixed(4)}</title>
          </circle>
        ))}

        {/* Connecting lines */}
        <polyline
          fill="none"
          stroke="#38bdf8"
          strokeWidth="1"
          opacity="0.3"
          points={validTrials.map(t => `${getX(t.number)},${getY(t.value as number)}`).join(' ')}
        />
      </svg>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 8, color: '#64748b', marginTop: 4 }}>
        <span>Min: {minVal.toFixed(2)}</span>
        <span>Max: {maxVal.toFixed(2)}</span>
      </div>
    </div>
  )
}
