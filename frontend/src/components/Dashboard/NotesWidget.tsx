import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { request } from '../../services/api'
import { Pin, Trash2, Plus, Loader2 } from 'lucide-react'

interface NotesWidgetProps {
  strategyId: number
}

interface Note {
  id: number
  content: string
  is_pinned: boolean
  created_at: string
}

export function NotesWidget({ strategyId }: NotesWidgetProps) {
  const queryClient = useQueryClient()
  const [newNoteContent, setNewNoteContent] = useState('')

  const { data: notes, isLoading } = useQuery({
    queryKey: ['notes', strategyId],
    queryFn: async () => {
      const res = await request<any>(`/api/notes/strategy/${strategyId}`)
      return res.data as Note[]
    },
    enabled: !!strategyId
  })

  const createNote = useMutation({
    mutationFn: async (content: string) => {
      return request(`/api/notes/strategy/${strategyId}`, { method: 'POST', body: JSON.stringify({ content, is_pinned: false }) })
    },
    onSuccess: () => {
      setNewNoteContent('')
      queryClient.invalidateQueries({ queryKey: ['notes', strategyId] })
    }
  })

  const togglePin = useMutation({
    mutationFn: async (note: Note) => {
      return request(`/api/notes/${note.id}`, { method: 'PUT', body: JSON.stringify({ is_pinned: !note.is_pinned }) })
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notes', strategyId] })
  })

  const deleteNote = useMutation({
    mutationFn: async (noteId: number) => {
      return request(`/api/notes/${noteId}`, { method: 'DELETE' })
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notes', strategyId] })
  })

  return (
    <div className="flex flex-col h-full bg-surface-container-low border-l border-outline-variant/30 text-on-surface font-body w-[350px]">
      <div className="p-4 border-b border-outline-variant/20 bg-surface-container">
        <h3 className="font-headline font-bold text-base">Strategy Notes</h3>
        <p className="font-label text-xs text-on-surface-variant">Notes shared across this strategy's runs</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading ? (
          <div className="flex justify-center py-8"><Loader2 className="w-6 h-6 animate-spin text-primary" /></div>
        ) : notes?.length === 0 ? (
          <p className="text-sm text-on-surface-variant text-center py-8">No notes yet. Add one below.</p>
        ) : (
          notes?.map(note => (
            <div key={note.id} className={`p-3 rounded-lg border ${note.is_pinned ? 'border-primary/50 bg-primary/5' : 'border-outline-variant/30 bg-surface-container'}`}>
              <div className="flex justify-between items-start gap-2 mb-2">
                <span className="text-[10px] font-label text-on-surface-variant">
                  {new Date(note.created_at).toLocaleString()}
                </span>
                <div className="flex gap-1">
                  <button 
                    onClick={() => togglePin.mutate(note)}
                    className={`p-1 rounded transition-colors ${note.is_pinned ? 'text-primary bg-primary/10' : 'text-on-surface-variant hover:bg-surface-container-high'}`}
                    title={note.is_pinned ? "Unpin" : "Pin"}
                  >
                    <Pin className="w-3.5 h-3.5" />
                  </button>
                  <button 
                    onClick={() => deleteNote.mutate(note.id)}
                    className="p-1 rounded text-on-surface-variant hover:text-error hover:bg-error/10 transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              <p className="text-xs whitespace-pre-wrap leading-relaxed">{note.content}</p>
            </div>
          ))
        )}
      </div>

      <div className="p-4 border-t border-outline-variant/20 bg-surface-container">
        <div className="flex flex-col gap-2">
          <textarea
            value={newNoteContent}
            onChange={(e) => setNewNoteContent(e.target.value)}
            placeholder="Add a new note..."
            className="w-full bg-surface-container-low border border-outline-variant/40 rounded p-2 text-sm text-on-surface focus:outline-hidden focus:border-primary resize-none h-20"
          />
          <button
            onClick={() => createNote.mutate(newNoteContent)}
            disabled={!newNoteContent.trim() || createNote.isPending}
            className="w-full bg-primary text-on-primary font-label text-sm font-semibold py-2 rounded hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {createNote.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            Add Note
          </button>
        </div>
      </div>
    </div>
  )
}
