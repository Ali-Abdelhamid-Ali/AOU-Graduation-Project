import { describe, expect, it } from 'vitest';

import { sanitizeHTML, validateRedirect } from './securityUtils';


describe('securityUtils', () => {
    it('blocks deceptive subdomain redirects', () => {
        expect(validateRedirect('https://evilbiointellect.com/path')).toBe('/');
    });

    it('allows exact domain redirects', () => {
        expect(validateRedirect('/clinical')).toBe('/clinical');
    });

    it('removes inline style attributes from sanitized html', () => {
        const sanitized = sanitizeHTML('<span class="note" style="color:red">Hello</span>');

        expect(sanitized).toContain('class="note"');
        expect(sanitized).not.toContain('style=');
    });
});