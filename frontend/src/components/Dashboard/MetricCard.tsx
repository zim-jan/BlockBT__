import { LucideIcon } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string | number
  status: 'positive' | 'negative' | 'neutral'
  icon?: LucideIcon
}

export function MetricCard({ title, value, status, icon: Icon }: MetricCardProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'positive':
        return 'text-secondary bg-secondary/10 shadow-[0_0_15px_rgba(92,253,128,0.15)]'
      case 'negative':
        return 'text-tertiary bg-tertiary/10 shadow-[0_0_15px_rgba(255,112,118,0.15)]'
      default:
        return 'text-on-surface-variant bg-surface-container-high'
    }
  }

  const getStatusBorder = () => {
    switch (status) {
      case 'positive':
        return 'border-l-secondary'
      case 'negative':
        return 'border-l-tertiary'
      default:
        return 'border-l-outline-variant/50'
    }
  }

  return (
    <div className={`bg-surface-container border border-outline-variant/20 p-6 flex flex-col justify-between relative overflow-hidden group hover:bg-surface-container-high transition-colors ${getStatusBorder()} border-l-2`}>
      <div className="flex justify-between items-start mb-4">
        <h3 className="font-label text-xs font-medium text-on-surface-variant tracking-wider uppercase">{title}</h3>
        {Icon && (
          <div className={`p-2 rounded-none ${getStatusColor()}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="font-headline text-3xl font-bold text-on-surface tracking-tight">
          {value}
        </span>
      </div>

      {/* Subtle background glow effect on hover */}
      <div className="absolute top-0 right-0 -mt-10 -mr-10 w-32 h-32 bg-primary opacity-0 group-hover:opacity-5 blur-3xl transition-opacity pointer-events-none rounded-full" />
    </div>
  )
}
