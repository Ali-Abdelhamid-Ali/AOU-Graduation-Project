import React from 'react'
import { brandingConfig } from '../config/brandingConfig'

/**
 * ErrorBoundary Component
 * 
 * Prevents the entire application from crashing on component-level errors.
 * Provides a production-ready fallback UI.
 */
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props)
        this.state = { hasError: false, error: null }
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error }
    }

    componentDidCatch(error, errorInfo) {
        console.error('Production Error Caught:', error, errorInfo)
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{
                    height: '100vh',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    textAlign: 'center',
                    padding: '2rem',
                    background: 'var(--color-background)',
                    color: 'var(--color-text)'
                }}>
                    <h1 style={{ color: 'var(--color-error)', fontSize: '3rem' }}>⚠️</h1>
                    <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Clinical System Error</h2>
                    <p style={{ maxWidth: '500px', color: 'var(--color-text-muted)', marginBottom: '2rem' }}>
                        We apologize for the inconvenience. {brandingConfig.brandName} encountered a technical exception.
                        The clinical data remains secure.
                    </p>
                    <button
                        onClick={() => window.location.reload()}
                        style={{
                            padding: '0.75rem 2rem',
                            background: 'var(--color-primary)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontWeight: '600'
                        }}
                    >
                        Restart Application
                    </button>
                </div>
            )
        }

        return this.props.children
    }
}

export default ErrorBoundary
