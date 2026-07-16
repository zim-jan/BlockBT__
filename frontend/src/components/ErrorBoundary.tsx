/**
 * Globalna granica błędów renderu (review 2026-07-16).
 *
 * Bez niej każdy nieobsłużony wyjątek w renderze odmontowywał całe drzewo
 * Reacta — użytkownik widział pusty <div id="root"> zamiast aplikacji.
 * Fallback pokazuje treść błędu (do zgłoszenia) i pozwala wrócić do widoku.
 */
import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught a render error:', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 24, maxWidth: 720, margin: '48px auto', fontFamily: 'monospace' }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: '#f87171', marginBottom: 8 }}>
            Something went wrong
          </h2>
          <pre
            style={{
              whiteSpace: 'pre-wrap',
              fontSize: 12,
              background: 'rgba(248, 113, 113, 0.08)',
              border: '1px solid rgba(248, 113, 113, 0.4)',
              borderRadius: 8,
              padding: 12,
              marginBottom: 12,
            }}
          >
            {this.state.error.message}
          </pre>
          <button
            onClick={() => this.setState({ error: null })}
            style={{
              padding: '6px 16px',
              borderRadius: 6,
              border: '1px solid #94a3b8',
              cursor: 'pointer',
            }}
          >
            Reload view
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
