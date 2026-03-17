/**
 * brandingConfig.js
 * 
 * The central configuration for hospital branding and identity.
 * Reverted to English-only as per user request.
 */

export const brandingConfig = {
    // Identity
    brandName: 'BioIntellect',
    hospitalName: 'Saudi German Hospital',
    tagline: 'Precision Medicine & Hospital Intelligence',
    shortDescription: 'BioIntellect is a state-of-the-art clinical intelligence platform powered by Saudi German Health to provide world-class healthcare delivery.',

    // Contact Info
    contact: {
        phone: '+20 02 26252400',
        emergency: '16259',
        email: 'info.egypt@sghgroup.net',
        address: 'Joseph Tito St, El Nozha, Cairo, Egypt',
        supportEmail: 'sghcare@sghegy.com'
    },

    // Platform Highlights
    platformHighlights: [
        {
            value: 'ECG + MRI',
            label: 'Clinical Workflows'
        },
        {
            value: 'Role-Based',
            label: 'Access Control'
        },
        {
            value: 'API-Backed',
            label: 'Operational Modules'
        },
        {
            value: 'Audit-Aware',
            label: 'Security Posture'
        }
    ],

    // Institutional Links
    links: {
        officialWebsite: 'https://sghgroup.com.eg',
        portalName: 'SGH Patient Portal'
    },

    // Creative Assets
    assets: {
        logo: '/src/assets/images/BioIntellect.png',
        heroBg: 'medical_hero_bg',
        textureBg: 'medical_texture_bg'
    }
}
