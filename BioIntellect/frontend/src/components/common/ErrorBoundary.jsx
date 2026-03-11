import React from 'react'
import { brandingConfig } from '@/config/brandingConfig'

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null,
            detailsLogged: false
        }
        this.handleReload = this.handleReload.bind(this)
        this.handleShowDetails = this.handleShowDetails.bind(this)
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error }
    }

    componentDidCatch(error, errorInfo) {
        this.setState({ errorInfo, detailsLogged: false })

        const errorDetails = {
            message: error?.message,
            stack: error?.stack,
            componentStack: errorInfo?.componentStack,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            userAgent: navigator.userAgent
        }

        console.error('[ErrorBoundary] Production error caught', errorDetails)

        try {
            localStorage.setItem('biointellect_last_error', JSON.stringify(errorDetails))
        } catch (storageError) {
            console.error('[ErrorBoundary] Failed to persist error details', storageError)
        }
    }

    handleReload() {
        window.location.reload()
    }

    handleShowDetails() {
        const { error, errorInfo } = this.state
        console.error('[ErrorBoundary] Console details requested', {
            error,
            errorInfo,
        })
        this.setState({ detailsLogged: true })
    }

    render() {
        if (!this.state.hasError) {
            return this.props.children
        }

        const { error, errorInfo, detailsLogged } = this.state

        return (
            <div
                style={{
                    minHeight: '100vh',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    textAlign: 'center',
                    padding: '2rem',
                    background: 'var(--color-background)',
                    color: 'var(--color-text)',
                    overflow: 'auto'
                }}
            >
                <h1 style={{ color: 'var(--color-error)', fontSize: '3rem', marginBottom: '0.5rem' }}>System Error</h1>
                <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Clinical workspace interrupted</h2>
                <p style={{ maxWidth: '560px', color: 'var(--color-text-muted)', marginBottom: '2rem' }}>
                    {brandingConfig.brandName} encountered an unexpected client-side exception. Clinical data remains protected.
                </p>

                <div
                    style={{
                        maxWidth: '800px',
                        width: '100%',
                        textAlign: 'left',
                        background: 'var(--color-surface)',
                        padding: '1.5rem',
                        borderRadius: '8px',
                        marginBottom: '2rem',
                        border: '1px solid var(--color-border)',
                        fontSize: '0.9rem'
                    }}
                >
                    <h3 style={{ marginTop: 0, marginBottom: '1rem', color: 'var(--color-primary)' }}>
                        Error Details
                    </h3>

                    {error ? (
                        <div style={{ marginBottom: '1rem' }}>
                            <strong>Error Message:</strong>
                            <div
                                style={{
                                    background: 'var(--color-background)',
                                    padding: '0.5rem',
                                    borderRadius: '4px',
                                    overflow: 'auto',
                                    maxHeight: '150px',
                                    fontSize: '0.85rem',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word'
                                }}
                            >
                                {error.message || 'No error message'}
                            </div>
                        </div>
                    ) : null}

                    {error?.stack ? (
                        <div style={{ marginBottom: '1rem' }}>
                            <strong>Error Stack:</strong>
                            <div
                                style={{
                                    background: 'var(--color-background)',
                                    padding: '0.5rem',
                                    borderRadius: '4px',
                                    overflow: 'auto',
                                    maxHeight: '200px',
                                    fontSize: '0.75rem',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word'
                                }}
                            >
                                {error.stack}
                            </div>
                        </div>
                    ) : null}

                    {errorInfo?.componentStack ? (
                        <div style={{ marginBottom: '1rem' }}>
                            <strong>Component Stack:</strong>
                            <div
                                style={{
                                    background: 'var(--color-background)',
                                    padding: '0.5rem',
                                    borderRadius: '4px',
                                    overflow: 'auto',
                                    maxHeight: '200px',
                                    fontSize: '0.75rem',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word'
                                }}
                            >
                                {errorInfo.componentStack}
                            </div>
                        </div>
                    ) : null}

                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                        <strong>Timestamp:</strong> {new Date().toISOString()}
                        <br />
                        <strong>URL:</strong> {window.location.href}
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                    <button
                        onClick={this.handleReload}
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
                    <button
                        onClick={this.handleShowDetails}
                        style={{
                            padding: '0.75rem 2rem',
                            background: 'var(--color-surface)',
                            color: 'var(--color-text)',
                            border: '1px solid var(--color-border)',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            fontWeight: '600'
                        }}
                    >
                        Show Details in Console
                    </button>
                </div>

                {detailsLogged ? (
                    <p style={{ marginTop: '1rem', color: 'var(--color-text-muted)' }}>
                        Error details were written to the browser console.
                    </p>
                ) : null}
            </div>
        )
    }
}

export default ErrorBoundary
