import React from 'react'
import { brandingConfig } from '@/config/brandingConfig'

/**
 * ErrorBoundary Component
 * 
 * Prevents the entire application from crashing on component-level errors.
 * Provides a production-ready fallback UI with detailed error logging.
 */
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props)
        this.state = { hasError: false, error: null, errorInfo: null }
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error }
    }

    componentDidCatch(error, errorInfo) {
        console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        console.error('🚨 [ERROR BOUNDARY] Production Error Caught')
        console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        console.error('Error Message:', error?.message)
        console.error('Error Stack:', error?.stack)
        console.error('Component Stack:', errorInfo?.componentStack)
        console.error('Error Object:', errorInfo)
        console.error('Timestamp:', new Date().toISOString())
        console.error('User Agent:', navigator.userAgent)
        console.error('URL:', window.location.href)
        console.error('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        
        // Try to save error details to localStorage for debugging
        try {
            const errorDetails = {
                message: error?.message,
                stack: error?.stack,
                componentStack: errorInfo?.componentStack,
                timestamp: new Date().toISOString(),
                url: window.location.href,
                userAgent: navigator.userAgent
            }
            localStorage.setItem('biointellect_last_error', JSON.stringify(errorDetails))
        } catch (e) {
            console.error('Failed to save error to localStorage:', e)
        }
    }

    render() {
        if (this.state.hasError) {
            const error = this.state.error
            const errorInfo = this.state.errorInfo
            
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
                    color: 'var(--color-text)',
                    overflow: 'auto'
                }}>
                    <h1 style={{ color: 'var(--color-error)', fontSize: '3rem' }}>⚠️</h1>
                    <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Clinical System Error</h2>
                    <p style={{ maxWidth: '500px', color: 'var(--color-text-muted)', marginBottom: '2rem' }}>
                        We apologize for the inconvenience. {brandingConfig.brandName} encountered a technical exception.
                        The clinical data remains secure.
                    </p>
                    
                    {/* Error Details Section */}
                    <div style={{
                        maxWidth: '800px',
                        width: '100%',
                        textAlign: 'left',
                        background: 'var(--color-surface)',
                        padding: '1.5rem',
                        borderRadius: '8px',
                        marginBottom: '2rem',
                        border: '1px solid var(--color-border)',
                        fontSize: '0.9rem'
                    }}>
                        <h3 style={{ marginTop: 0, marginBottom: '1rem', color: 'var(--color-primary)' }}>
                            Error Details (for debugging)
                        </h3>
                        
                        {error && (
                            <div style={{ marginBottom: '1rem' }}>
                                <strong>Error Message:</strong>
                                <div style={{
                                    background: 'var(--color-background)',
                                    padding: '0.5rem',
                                    borderRadius: '4px',
                                    overflow: 'auto',
                                    maxHeight: '150px',
                                    fontSize: '0.85rem',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word'
                                }}>
                                    {error.message || 'No error message'}
                                </div>
                            </div>
                        )}
                        
                        {error?.stack && (
                            <div style={{ marginBottom: '1rem' }}>
                                <strong>Error Stack:</strong>
                                <div style={{
                                    background: 'var(--color-background)',
                                    padding: '0.5rem',
                                    borderRadius: '4px',
                                    overflow: 'auto',
                                    maxHeight: '200px',
                                    fontSize: '0.75rem',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word'
                                }}>
                                    {error.stack}
                                </div>
                            </div>
                        )}
                        
                        {errorInfo?.componentStack && (
                            <div style={{ marginBottom: '1rem' }}>
                                <strong>Component Stack:</strong>
                                <div style={{
                                    background: 'var(--color-background)',
                                    padding: '0.5rem',
                                    borderRadius: '4px',
                                    overflow: 'auto',
                                    maxHeight: '200px',
                                    fontSize: '0.75rem',
                                    whiteSpace: 'pre-wrap',
                                    wordBreak: 'break-word'
                                }}>
                                    {errorInfo.componentStack}
                                </div>
                            </div>
                        )}
                        
                        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                            <strong>Timestamp:</strong> {new Date().toISOString()}<br />
                            <strong>URL:</strong> {window.location.href}
                        </div>
                    </div>
                    
                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <button
                            onClick={() => window.location.reload()}
                            style={{
                                padding: '0.75rem 2rem',
                                background: 'var(--color-primary)',
                                color: 'white',
                                border: 'none',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                fontWeight: '600',
                                marginRight: '1rem'
                            }}
                        >
                            Restart Application
                        </button>
                        <button
                            onClick={() => {
                                console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
                                console.log('📋 [ERROR BOUNDARY] User clicked "Show Details"')
                                console.log('Error:', error)
                                console.log('ErrorInfo:', errorInfo)
                                console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
                                alert('Error details logged to browser console. Press F12 to view.')
                            }}
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
                </div>
            )
        }

        return this.props.children
    }
}

export default ErrorBoundary
