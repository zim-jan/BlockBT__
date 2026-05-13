import React from 'react'
import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock ResizeObserver
class ResizeObserver {
  callback: ResizeObserverCallback
  constructor(callback: ResizeObserverCallback) {
    this.callback = callback
  }
  observe(target: Element) {
    // Simulate the observer trigger
    setTimeout(() => {
      this.callback([{ target } as ResizeObserverEntry], this)
    }, 0)
  }
  unobserve() {}
  disconnect() {}
}

// Mock DOMMatrixReadOnly
class DOMMatrixReadOnly {
  m22: number
  constructor(transform?: string) {
    const scale = transform?.match(/scale\(([1-9.])\)/)?.[1]
    this.m22 = scale !== undefined ? +scale : 1
  }
}

// Apply mocks to global object
global.ResizeObserver = ResizeObserver
global.DOMMatrixReadOnly = DOMMatrixReadOnly as any

// Mock offsetHeight/Width which JSDOM returns as 0
Object.defineProperties(global.HTMLElement.prototype, {
  offsetHeight: { get() { return parseFloat(this.style.height) || 1 } },
  offsetWidth: { get() { return parseFloat(this.style.width) || 1 } },
})

// Mock SVG getBBox
if (!global.SVGElement.prototype.getBBox) {
  global.SVGElement.prototype.getBBox = () => ({
    x: 0,
    y: 0,
    width: 0,
    height: 0,
    bottom: 0,
    left: 0,
    right: 0,
    top: 0,
    toJSON: () => ({}),
  })
}

// Mock Plotly (react-plotly.js) since it requires a real DOM/WebGL
vi.mock('react-plotly.js', () => ({
  default: () => <div data-testid="mock-plotly" />,
}))
