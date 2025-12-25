/**
 * options.js
 * 
 * Centralized dropdown options for clinical and administrative forms.
 * Aligned with BioIntellect SQL Schema Enums and Seed Data.
 */

export const specialtyOptions = [
    { value: 'CARD', label: 'Cardiology' },
    { value: 'NEUR', label: 'Neurology' },
    { value: 'PNEU', label: 'Pulmonology' },
    { value: 'GAST', label: 'Gastroenterology' },
    { value: 'NEPH', label: 'Nephrology' },
    { value: 'ENDO', label: 'Endocrinology' },
    { value: 'RHEU', label: 'Rheumatology' },
    { value: 'HEMA', label: 'Hematology' },
    { value: 'ONCO', label: 'Oncology' },
    { value: 'INFD', label: 'Infectious Disease' },
    { value: 'DERM', label: 'Dermatology' },
    { value: 'PEDI', label: 'Pediatrics' },
    { value: 'GERI', label: 'Geriatrics' },
    { value: 'INTM', label: 'Internal Medicine' },
    { value: 'FMED', label: 'Family Medicine' },
    { value: 'PSYC', label: 'Psychiatry' },
    { value: 'EMER', label: 'Emergency Medicine' },
    { value: 'ICME', label: 'Intensive Care Medicine' },
    { value: 'GENSURG', label: 'General Surgery' }
];

export const adminOptions = [
    { value: 'super_admin', label: 'Super Admin' },
    { value: 'admin', label: 'Admin' }
];

export const nurseOptions = [
    { value: 'nurse', label: 'Nurse' }
];

export const genderOptions = [
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' },
    { value: 'other', label: 'Other' }
];

export const bloodTypeOptions = [
    { value: 'A+', label: 'A+' },
    { value: 'A-', label: 'A-' },
    { value: 'B+', label: 'B+' },
    { value: 'B-', label: 'B-' },
    { value: 'AB+', label: 'AB+' },
    { value: 'AB-', label: 'AB-' },
    { value: 'O+', label: 'O+' },
    { value: 'O-', label: 'O-' },
    { value: 'unknown', label: 'Unknown' }
];
