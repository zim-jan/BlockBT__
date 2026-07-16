/**
 * CategoryBadge — displays the DAG architectural category on each node.
 * Uses color-coding aligned with Phase 9 architecture layers.
 */

import type { NodeCategory } from '../../../types/types'

const CATEGORY_STYLES: Record<NodeCategory, { bg: string; color: string; label: string }> = {
  DataIngestion:  { bg: '#1e3a5f', color: '#7cc4fa', label: 'Data' },
  Indicators:     { bg: '#3b2f1e', color: '#f5c542', label: 'Indicator' },
  LogicOperators: { bg: '#1e3b2f', color: '#6ee7b7', label: 'Logic' },
  Execution:      { bg: '#3b1e2f', color: '#f472b6', label: 'Execution' },
  Meta:           { bg: '#2f1e3b', color: '#c084fc', label: 'Meta' },
}

interface Props {
  category: NodeCategory
}

export function CategoryBadge({ category }: Props) {
  const style = CATEGORY_STYLES[category]
  if (!style) return null

  return (
    <span
      style={{
        display: 'inline-block',
        fontSize: '9px',
        fontWeight: 600,
        letterSpacing: '0.5px',
        textTransform: 'uppercase',
        padding: '2px 6px',
        borderRadius: '3px',
        backgroundColor: style.bg,
        color: style.color,
        lineHeight: '1.4',
      }}
    >
      {style.label}
    </span>
  )
}
