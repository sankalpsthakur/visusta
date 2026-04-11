'use client'

import React from 'react'
import { AlertTriangle } from 'lucide-react'

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  override render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div
          className="rounded-lg p-6 flex flex-col items-center gap-3 text-center"
          style={{
            background: 'var(--bg-surface)',
            border: '1px solid color-mix(in srgb, var(--severity-critical) 25%, transparent)',
          }}
        >
          <AlertTriangle className="w-5 h-5" style={{ color: 'var(--severity-critical)' }} />
          <div>
            <p className="text-sm font-medium mb-1" style={{ color: 'var(--text-primary)' }}>
              Something went wrong
            </p>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              {this.state.error?.message ?? 'An unexpected error occurred'}
            </p>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
