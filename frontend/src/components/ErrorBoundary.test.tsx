import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ErrorBoundary } from './ErrorBoundary'

function Bomb(): never {
  throw new Error('kaboom during render')
}

describe('ErrorBoundary', () => {
  // React loguje błędy boundary do console.error — wyciszamy szum w testach
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders children when nothing throws', () => {
    render(
      <ErrorBoundary>
        <div>zdrowa aplikacja</div>
      </ErrorBoundary>
    )
    expect(screen.getByText('zdrowa aplikacja')).toBeInTheDocument()
  })

  it('renders fallback with error message instead of unmounting the tree', () => {
    render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>
    )
    // Zamiast pustego #root: czytelny komunikat + treść błędu do zgłoszenia
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
    expect(screen.getByText(/kaboom during render/)).toBeInTheDocument()
  })

  it('reset button clears the error state and re-renders children', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>
    )
    // Podmieniamy dzieci na zdrowe (fallback dalej widoczny), potem reset
    rerender(
      <ErrorBoundary>
        <div>po resecie</div>
      </ErrorBoundary>
    )
    fireEvent.click(screen.getByRole('button', { name: /reload/i }))
    expect(screen.getByText('po resecie')).toBeInTheDocument()
  })
})
