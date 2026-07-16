import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock ResizeObserver — entry musi mieć contentRect/borderBoxSize:
// @xyflow/system >= 0.0.79 czyta entry.contentRect.width w extentResizeObserver
// i niepełny mock generował unhandled TypeError w testach (review 2026-07-16)
const makeResizeObserverEntry = (target: Element): ResizeObserverEntry => {
  const size = { inlineSize: 1, blockSize: 1 }
  const rect = {
    width: 1,
    height: 1,
    x: 0,
    y: 0,
    top: 0,
    left: 0,
    bottom: 1,
    right: 1,
    toJSON: () => ({}),
  } as DOMRectReadOnly
  return {
    target,
    contentRect: rect,
    borderBoxSize: [size],
    contentBoxSize: [size],
    devicePixelContentBoxSize: [size],
  } as unknown as ResizeObserverEntry
}

class ResizeObserver {
  callback: ResizeObserverCallback
  constructor(callback: ResizeObserverCallback) {
    this.callback = callback
  }
  observe(target: Element) {
    // Simulate the observer trigger
    setTimeout(() => {
      this.callback([makeResizeObserverEntry(target)], this)
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
globalThis.ResizeObserver = ResizeObserver
globalThis.DOMMatrixReadOnly = DOMMatrixReadOnly as any

// Mock offsetHeight/Width which JSDOM returns as 0
Object.defineProperties(globalThis.HTMLElement.prototype, {
  offsetHeight: { get() { return parseFloat(this.style.height) || 1 } },
  offsetWidth: { get() { return parseFloat(this.style.width) || 1 } },
})

// Mock SVG getBBox
if (!(globalThis.SVGElement.prototype as any).getBBox) {
  ;(globalThis.SVGElement.prototype as any).getBBox = () => ({
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
  default: () => null,
}))
