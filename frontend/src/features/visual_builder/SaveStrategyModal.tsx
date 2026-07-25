import React, { useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '../../services/api'
import { useWorkflowStore } from '../../store/workflowStore'
import { showToast } from '../../store/useToastStore'
import { X, Save } from 'lucide-react'

interface SaveStrategyModalProps {
  isOpen: boolean
  onClose: () => void
}

export const SaveStrategyModal: React.FC<SaveStrategyModalProps> = ({ isOpen, onClose }) => {
  const nodes = useWorkflowStore((s) => s.nodes)
  const edges = useWorkflowStore((s) => s.edges)
  const exportDAG = useWorkflowStore((s) => s.exportDAG)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  console.log('[SaveStrategyModal] Render, isOpen:', isOpen)

  if (!isOpen) return null

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      showToast.warning('Name required', 'Enter a strategy name before saving.')
      return
    }

    setIsSubmitting(true)
    console.log('[SaveStrategyModal] 💾 Initiating strategy save:', { name, description, nodesCount: nodes.length, edgesCount: edges.length })

    try {
      const dagPayload = exportDAG()
      console.log('[SaveStrategyModal] Serialized DAG payload:', dagPayload)

      const res = await api.strategies.create({
        name: name.trim(),
        description: description.trim(),
        parameters: { nodes, edges },
        code_content: JSON.stringify(dagPayload),
      } as any)

      console.log('[SaveStrategyModal] ✅ API response:', res)

      if (res && res.success) {
        showToast.success('Strategy Saved', `Strategy "${name}" has been saved to database.`)
        setName('')
        setDescription('')
        onClose()
      } else {
        const errStr = res?.error || 'Unknown server error'
        showToast.error('Save error', `Failed to save strategy: ${errStr}`)
      }
    } catch (err) {
      console.error('[SaveStrategyModal] ❌ Exception during strategy save:', err)
      showToast.error('Save error', `An exception occurred: ${(err as Error).message || 'Connection error'}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  return createPortal(
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(4px)',
        zIndex: 99999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div className="bg-[#131722] border border-white/10 rounded-2xl w-full max-w-lg p-6 shadow-2xl text-slate-100 space-y-5" style={{ backgroundColor: '#131722' }}>
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-lg">
            <Save className="w-5 h-5" />
            <span>Save DAG Strategy</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Strategy Name *</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Momentum SMA (AAPL, MSFT)"
              className="w-full bg-[#0b0d14] border border-white/10 rounded-lg px-3 py-2.5 text-sm text-slate-100 focus:outline-hidden focus:border-indigo-500 font-medium"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Description (optional)</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe tactical assumptions, indicators, and parameters..."
              className="w-full bg-[#0b0d14] border border-white/10 rounded-lg p-3 text-sm text-slate-100 focus:outline-hidden focus:border-indigo-500 resize-none"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 rounded-lg text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : 'Save Strategy'}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  )
}
