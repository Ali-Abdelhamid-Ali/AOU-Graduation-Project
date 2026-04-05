import securityIcon from '@/assets/images/icons/security.png'
import insightsIcon from '@/assets/images/icons/insights.png'
import cardioIcon from '@/assets/images/icons/cardio.png'
import neuroIcon from '@/assets/images/icons/neuro.png'

const dashboardColors = {
    admin: 'var(--color-accent)',
    staff: 'var(--color-secondary)',
    danger: 'var(--color-error)',
    primary: 'var(--color-primary)',
    indigo: 'var(--color-info-dark)'
}

export const getAdminCards = (userSpecialty, handlers) => {
    const {
        onCreateDoctor,
        onCreateAdmin,
        onEcgAnalysis,
        onMriSegmentation,
        onMedicalLlm
    } = handlers;

    const cards = [
        {
            id: 'admins',
            title: 'Administrative Control',
            description: 'Provision administrative accounts and manage system-wide security policies.',
            icon: securityIcon,
            action: onCreateAdmin,
            color: dashboardColors.admin,
            tag: 'ROOT',
            restricted: true
        },
        {
            id: 'doctors',
            title: 'Clinical Practitioner Registry',
            description: 'Manage medical staff credentials, specialized access levels, and department assignments.',
            icon: securityIcon,
            action: onCreateDoctor,
            color: dashboardColors.staff,
            tag: 'STAFF',
            restricted: true
        },
        {
            id: 'ecg',
            title: 'AI Cardiac Diagnostics (ECG)',
            description: 'CNN-Transformer based arrhythmia classification. Prioritized for Cardiologists.',
            icon: cardioIcon,
            action: onEcgAnalysis,
            color: dashboardColors.danger,
            tag: 'CARDIOLOGY',
            priority: userSpecialty === 'cardiology' || userSpecialty === 'cardio',
            clinical: true
        },
        {
            id: 'mri',
            title: 'AI Neuro-Imaging (MRI)',
            description: '3D U-Net powered brain tumor segmentation. Prioritized for Neurologists.',
            icon: neuroIcon,
            action: onMriSegmentation,
            color: dashboardColors.primary,
            tag: 'NEUROLOGY',
            priority: userSpecialty === 'neurology' || userSpecialty === 'neuro',
            clinical: true
        },
        {
            id: 'proj',
            title: 'Clinical Advisor LLM',
            description: 'Interactive AI decision support for diagnosis validation and medical knowledge.',
            icon: insightsIcon,
            action: onMedicalLlm,
            color: dashboardColors.indigo,
            tag: 'ADVISOR',
            clinical: true
        }
    ];

    return cards;
};
