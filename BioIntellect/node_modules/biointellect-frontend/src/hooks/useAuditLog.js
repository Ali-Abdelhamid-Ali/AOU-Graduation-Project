import { useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

/**
 * useAuditLog Hook
 * Standardizes clinical event tracking across the platform.
 * Production requirement: Track all diagnostic and sensitive data access.
 */
export const useAuditLog = () => {
    const { currentUser } = useAuth();

    const logEvent = useCallback((action, metadata = {}) => {
        const timestamp = new Date().toISOString();
        const eventData = {
            timestamp,
            user_id: currentUser?.id || 'anonymous',
            user_role: currentUser?.user_role || 'unknown',
            action,
            metadata,
            environment: import.meta.env.MODE,
            url: window.location.href
        };

        // In production, this would send to a secure logging endpoint (e.g., Supabase table)
        console.group(`[AUDIT_LOG] ${action}`);
        console.info('Timestamp:', eventData.timestamp);
        console.info('Principal:', eventData.user_id);
        console.info('Metadata:', eventData.metadata);
        console.groupEnd();

        // Optional: Persist locally for session session analysis
        const sessionLogs = JSON.parse(sessionStorage.getItem('clinical_audit_logs') || '[]');
        sessionLogs.push(eventData);
        sessionStorage.setItem('clinical_audit_logs', JSON.stringify(sessionLogs.slice(-50))); // Keep last 50
    }, [currentUser]);

    return { logEvent };
};
