import { useState, useEffect } from 'react';

/**
 * useFormPersistence Hook
 * Automatically mirrors state to sessionStorage to protect against accidental refreshes.
 * 
 * @param {string} key - Unique key for storage
 * @param {any} initialValue - Default state
 * @returns {Array} [state, setState]
 */
export const useFormPersistence = (key, initialValue) => {
    // 1. Initialize state from storage if exists, else use initialValue
    const [state, setState] = useState(() => {
        try {
            const saved = sessionStorage.getItem(`form_persistance_${key}`);
            return saved ? JSON.parse(saved) : initialValue;
        } catch (error) {
            console.error('SessionStorage access error:', error);
            return initialValue;
        }
    });

    // 2. Sync state to storage whenever it changes
    useEffect(() => {
        try {
            sessionStorage.setItem(`form_persistance_${key}`, JSON.stringify(state));
        } catch (error) {
            console.error('SessionStorage write error:', error);
        }
    }, [key, state]);

    // 3. Clear storage helper (called on successful submission)
    const clearStorage = () => {
        sessionStorage.removeItem(`form_persistance_${key}`);
    };

    return [state, setState, clearStorage];
};
