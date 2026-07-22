import React from 'react'
import { useToastStore } from '../../store/useToastStore'
import type { ToastMessage } from '../../store/useToastStore'
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-react'

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToastStore()

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-md w-full pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  )
}

const ToastItem: React.FC<{ toast: ToastMessage; onClose: () => void }> = ({ toast, onClose }) => {
  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
      case 'info':
      default:
        return <Info className="w-5 h-5 text-indigo-400 shrink-0" />
    }
  }

  const getBorderColor = () => {
    switch (toast.type) {
      case 'success':
        return 'border-emerald-500/30'
      case 'error':
        return 'border-red-500/40'
      case 'warning':
        return 'border-amber-500/30'
      case 'info':
      default:
        return 'border-indigo-500/30'
    }
  }

  return (
    <div
      className={`pointer-events-auto flex items-start gap-3 p-4 rounded-xl bg-[#131722]/95 backdrop-blur-md border ${getBorderColor()} shadow-2xl text-slate-100 transition-all duration-300 animate-in slide-in-from-bottom-5`}
    >
      {getIcon()}
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-semibold text-slate-100">{toast.title}</h4>
        {toast.message && (
          <p className="text-xs text-slate-400 mt-1 leading-relaxed break-words">{toast.message}</p>
        )}
      </div>
      <button
        onClick={onClose}
        aria-label="Zamknij powiadomienie"
        className="p-1 rounded-lg hover:bg-slate-800/60 text-slate-400 hover:text-slate-200 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}
