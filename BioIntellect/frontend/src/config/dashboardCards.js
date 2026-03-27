import analyticsIcon from '@/assets/images/icons/analytics.png'
import securityIcon from '@/assets/images/icons/security.png'
import insightsIcon from '@/assets/images/icons/insights.png'
import cardioIcon from '@/assets/images/icons/cardio.png'
import neuroIcon from '@/assets/images/icons/neuro.png'

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
            color: '#f43f5e',
            tag: 'ROOT',
            restricted: true
        },
        {
            id: 'doctors',
            title: 'Clinical Practitioner Registry',
            description: 'Manage medical staff credentials, specialized access levels, and department assignments.',
            icon: securityIcon,
            action: onCreateDoctor,
            color: '#10b981',
            tag: 'STAFF',
            restricted: true
        },
        {
            id: 'ecg',
            title: 'AI Cardiac Diagnostics (ECG)',
            description: 'CNN-Transformer based arrhythmia classification. Prioritized for Cardiologists.',
            icon: cardioIcon,
            action: onEcgAnalysis,
            color: '#ef4444',
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
            color: '#3b82f6',
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
            color: '#6366f1',
            tag: 'ADVISOR',
            clinical: true
        }
    ];

    return cards;
};
