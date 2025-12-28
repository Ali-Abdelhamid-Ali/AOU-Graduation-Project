import DOMPurify from 'dompurify';
import { z } from 'zod';

/**
 * 🛡️ Security Utilities for BioIntellect
 * Implements defenses against XSS, Prototype Pollution, and Open Redirects.
 */

// 1. INPUT VALIDATION (ZOD SCHEMAS)
export const schemas = {
    patient: z.object({
        email: z.string().trim().email('Invalid medical email format'),
        first_name: z.string().trim().min(2, 'Name too short'),
        last_name: z.string().trim().min(2, 'Name too short'),
        phone: z.string().trim().regex(/^[\d\s+\-()]{7,}$/, 'Invalid phone format').optional().or(z.literal('')),
        date_of_birth: z.string().optional(),
    }).passthrough(),

    doctor: z.object({
        email: z.string().trim().email('Invalid clinical email'),
        first_name: z.string().trim().min(2, 'Name too short'),
        last_name: z.string().trim().min(2, 'Surname too short'),
        license_number: z.string().trim().min(3, 'Invalid license format').optional(),
    }).passthrough(),

    login: z.object({
        email: z.string().trim().email(),
        password: z.string().min(6),
    }).passthrough()
};

// 2. XSS PROTECTION
const sanitizerConfig = {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'span', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'class', 'style'],
};

/**
 * Sanitizes HTML content to prevent XSS attacks.
 * @param {string} dirty - The raw HTML string.
 * @returns {string} - The clean HTML string.
 */
export const sanitizeHTML = (dirty) => {
    if (!dirty) return '';
    return DOMPurify.sanitize(dirty, sanitizerConfig);
};

// 2. OPEN REDIRECT PROTECTION
const ALLOWED_DOMAINS = [
    window.location.hostname,
    'biointellect.com',
    'supabase.co',
];

/**
 * Validates a URL to prevent Open Redirect attacks.
 * @param {string} url - The URL to validate.
 * @returns {string} - The original URL if safe, otherwise redirects to home.
 */
export const validateRedirect = (url) => {
    try {
        if (!url) return '/';

        // Relative URLs are always allowed
        if (url.startsWith('/') && !url.startsWith('//')) {
            return url;
        }

        const urlObj = new URL(url);
        if (ALLOWED_DOMAINS.some(domain => urlObj.hostname.endsWith(domain))) {
            return url;
        }

        console.warn('🚨 [SECURITY]: Blocked unsafe redirect to:', url);
        return '/';
    } catch (e) {
        return '/';
    }
};

// 3. PROTOTYPE POLLUTION PROTECTION
/**
 * Safe object property setter to prevent Prototype Pollution.
 * @param {Object} obj - The target object.
 * @param {string} path - The property path.
 * @param {any} value - The value to set.
 */
export const safeSet = (obj, path, value) => {
    const keys = path.split('.');
    let current = obj;

    for (let i = 0; i < keys.length; i++) {
        const key = keys[i];

        // Block dangerous keys
        if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
            console.error('🚨 [SECURITY]: Prototype Pollution attempt blocked at key:', key);
            return;
        }

        if (i === keys.length - 1) {
            current[key] = value;
        } else {
            if (!current[key]) current[key] = {};
            current = current[key];
        }
    }
};

// 4. CSV FORMULA INJECTION PROTECTION
/**
 * Sanitizes a value before exporting to CSV to prevent formula injection.
 * @param {any} value - The value to sanitize.
 * @returns {string} - The sanitized string.
 */
export const sanitizeForCSV = (value) => {
    const str = String(value);
    if (/^[=+\-@\t\r]/.test(str)) {
        return `'${str}`; // Prefix with single quote to escape formula
    }
    return str;
};
