/**
 * formatters.js
 * 
 * Centralized formatting utilities for production-grade data display.
 */

/**
 * Formats a date string into a localized medical format.
 * @param {string} date - ISO date string
 * @param {string} locale - Locale override (default: 'en-US')
 */
export const formatDate = (date, locale = 'en-US') => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleDateString(locale, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
};

/**
 * Formats a Medical Record Number (MRN) for high legibility.
 * Example: MRN-2023-1234
 * @param {string} mrn 
 */
export const formatMRN = (mrn) => {
    if (!mrn) return '---';
    return mrn.toString().toUpperCase();
};

/**
 * Formats file sizes from bytes to KB/MB.
 */
export const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Capitalizes clinical terms for consistency.
 */
export const capitalize = (str) => {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};
