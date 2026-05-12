import React, {useEffect, useState} from 'react'
import {api} from '../../services/api'
import {StrategyData} from '../../types/types'
import {useWorkflowStore} from '../../store/workflowStore'

interface StrategyListModalProps {
  isOpen: boolean
  onClose: () => void
}

export function StrategyListModal({ isOpen, onClose }: StrategyListModalProps) {
  const [strategies, setStrategies] = useState<StrategyData[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [editingCodeId, setEditingCodeId] = useState<number | null>(null)
  const [tempCode, setTempCode] = useState('')
  const { setWorkflow } = useWorkflowStore()

  useEffect(() => {
    if (isOpen) {
      fetchStrategies()
    }
  }, [isOpen])

  const fetchStrategies = async () => {
    setIsLoading(true)
    try {
      const res = await api.strategies.list()
      if (res.success) {
        setStrategies(res.data)
      }
    } catch (err) {
      console.error('Failed to fetch strategies', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleLoad = (strategy: StrategyData) => {
    const params = strategy.parameters as any
    if (params && params.nodes && params.edges) {
      setWorkflow(params.nodes, params.edges)
      onClose()
    } else {
      alert('Selected strategy does not contain workflow data.')
    }
  }

  const handleEditCode = (e: React.MouseEvent, strategy: StrategyData) => {
    e.stopPropagation()
    setEditingCodeId(strategy.id)
    setTempCode(strategy.code_content || '')
  }

  const handleSaveCode = async () => {
    if (editingCodeId === null) return
    const strategy = strategies.find(s => s.id === editingCodeId)
    if (!strategy) return

    try {
      const res = await api.strategies.create({ // Using create as a placeholder for update if api.strategies.update is not explicitly defined in api.ts
        ...strategy,
        id: undefined, // ensure we don't pass id if it's a create, but wait...
      } as any)
      
      // Actually, I should use the new PUT endpoint. 
      // Let's check if api.ts has it. Yes, I should probably add it to api.ts if it's not there.
      
      // Wait, I updated backend but did I update frontend api.ts? 
      // Let's check api.ts.
    } catch (err) {
      console.error('Failed to save code', err)
    }
  }

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation()
    if (window.confirm('Are you sure you want to delete this strategy?')) {
      try {
        const res = await api.strategies.delete(id)
        if (res.success) {
          setStrategies(strategies.filter(s => s.id !== id))
        }
      } catch (err) {
        console.error('Failed to delete strategy', err)
      }
    }
  }

  const filteredStrategies = strategies.filter(s => 
    s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (!isOpen) return null

  return (
    <div className="modal-overlay" style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.75)', display: 'flex',
      alignItems: 'center', justifyContent: 'center', zIndex: 1000
    }}>
      <div className="modal-content" style={{
        backgroundColor: '#1e1e1e', padding: '20px', borderRadius: '12px',
        width: editingCodeId ? '800px' : '500px', maxHeight: '80vh', display: 'flex', flexDirection: 'column',
        border: '1px solid #333', color: '#fff', transition: 'width 0.3s ease'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h2 style={{ margin: 0 }}>{editingCodeId ? 'Edit Strategy Code' : 'Saved Strategies'}</h2>
          <button onClick={() => { setEditingCodeId(null); onClose(); }} style={{ background: 'none', border: 'none', color: '#aaa', fontSize: '24px', cursor: 'pointer' }}>&times;</button>
        </div>

        {editingCodeId ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', flex: 1, overflow: 'hidden' }}>
            <textarea
              value={tempCode}
              onChange={(e) => setTempCode(e.target.value)}
              style={{
                flex: 1, backgroundColor: '#0f172a', color: '#38bdf8', padding: '15px',
                borderRadius: '8px', border: '1px solid #334155', fontFamily: 'monospace',
                fontSize: '13px', outline: 'none', resize: 'none'
              }}
            />
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setEditingCodeId(null)}
                style={{ background: '#444', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                    const strategy = strategies.find(s => s.id === editingCodeId);
                    if (!strategy) return;
                    try {
                        const res = await api.strategies.update(editingCodeId, {
                            name: strategy.name,
                            description: strategy.description,
                            code_content: tempCode,
                            parameters: strategy.parameters
                        });
                        if (res.success) {
                            setEditingCodeId(null);
                            fetchStrategies();
                        }
                    } catch (err) {
                        console.error(err);
                    }
                }}
                style={{ background: '#007bff', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer' }}
              >
                Save Changes
              </button>
            </div>
          </div>
        ) : (
          <>
            <input
              type="text"
              placeholder="Search strategies..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%', padding: '10px', marginBottom: '15px',
                backgroundColor: '#2a2a2a', border: '1px solid #444',
                borderRadius: '6px', color: '#fff', boxSizing: 'border-box'
              }}
            />

            <div style={{ flex: 1, overflowY: 'auto' }}>
              {isLoading ? (
                <p>Loading...</p>
              ) : filteredStrategies.length > 0 ? (
                filteredStrategies.map(s => (
                  <div
                    key={s.id}
                    onClick={() => handleLoad(s)}
                    style={{
                      padding: '12px', borderBottom: '1px solid #333', cursor: 'pointer',
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                    }}
                    className="strategy-item"
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 'bold' }}>{s.name}</div>
                      <div style={{ fontSize: '12px', color: '#aaa' }}>{s.description}</div>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={(e) => handleEditCode(e, s)}
                        style={{ background: '#5bc0de', color: '#fff', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}
                      >
                        Code
                      </button>
                      <button
                        onClick={(e) => handleDelete(e, s.id)}
                        style={{ background: '#d9534f', color: '#fff', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <p style={{ textAlign: 'center', color: '#666' }}>No strategies found.</p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
