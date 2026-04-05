/**
 * Centralized Role Management Configuration
 * Defines all system roles, access levels, payload construction, and DATABASE MAPPINGS.
 */

// Core System Roles
export const ROLES = {
    SUPER_ADMIN: 'super_admin',
    ADMIN: 'administrator', // Database standard
    NURSE: 'nurse',
    DOCTOR: 'doctor',
    PATIENT: 'patient'
};

// Legacy/Frontend aliasing map (Frontend Role -> Database Role)
export const ROLE_ALIAS_MAP = {
    'admin': ROLES.ADMIN,
    'administrator': ROLES.ADMIN,
    'super_admin': ROLES.SUPER_ADMIN,
    'nurse': ROLES.NURSE,
    'doctor': ROLES.DOCTOR,
    'patient': ROLES.PATIENT
};

export const CLINICAL_ROLES = Object.values(ROLES);

/**
 * DATABASE MAPPING CONFIGURATION
 * Connects Auth Roles to specific Database Tables and Fields.
 * This acts as the Single Source of Truth for fetching user profiles.
 */
export const ROLE_DB_CONFIG = {
    [ROLES.PATIENT]: {
        table: 'patients',
        // Select logic: standard fields + hospital join
        select: `
            id, first_name, last_name, first_name_ar, last_name_ar,
            user_id, hospital_id, hospitals(hospital_name_en), 
            mrn, avatar_url, date_of_birth, gender, phone, 
            address, city, country_id, region_id,
            blood_type, national_id, passport_number,
            insurance_provider, insurance_number,
            emergency_contact_name, emergency_contact_phone, emergency_contact_relation,
            allergies, chronic_conditions, current_medications, notes
        `,
        transform: (data) => ({
            id: data.id,
            first_name: data.first_name,
            last_name: data.last_name,
            first_name_ar: data.first_name_ar,
            last_name_ar: data.last_name_ar,
            full_name: `${data.first_name} ${data.last_name}`,
            user_role: ROLES.PATIENT,
            hospital_id: data.hospital_id,
            hospital_name: data.hospitals?.hospital_name_en,
            mrn: data.mrn || data.medical_record_number,
            photo_url: data.photo_url || data.avatar_url,
            avatar_url: data.avatar_url || data.photo_url,
            date_of_birth: data.date_of_birth,
            gender: data.gender,
            phone: data.phone,
            address: data.address,
            city: data.city,
            country_id: data.country_id,
            region_id: data.region_id,
            blood_type: data.blood_type,
            national_id: data.national_id,
            passport_number: data.passport_number,
            insurance_provider: data.insurance_provider,
            insurance_number: data.insurance_number,
            emergency_contact_name: data.emergency_contact_name,
            emergency_contact_phone: data.emergency_contact_phone,
            emergency_contact_relation: data.emergency_contact_relation,
            allergies: data.allergies || [],
            chronic_conditions: data.chronic_conditions || [],
            current_medications: data.current_medications || [],
            notes: data.notes
        })
    },
    [ROLES.DOCTOR]: {
        table: 'doctors',
        // Joined specialty for specialty-based dashboard logic
        select: `
            id, first_name, last_name, user_id, hospital_id, 
            hospitals(hospital_name_en),
            doctor_specialties(
                is_primary,
                specialty_types(specialty_code, specialty_name_en)
            )
        `,
        transform: (data) => {
            // Find primary specialty or fallback to first one
            const primarySpec = data.doctor_specialties?.find(s => s.is_primary) || data.doctor_specialties?.[0];
            const specialty = primarySpec?.specialty_types?.specialty_code || null;
            const specialtyName = primarySpec?.specialty_types?.specialty_name_en || 'General Practitioner';

            return {
                id: data.id,
                first_name: data.first_name,
                last_name: data.last_name,
                full_name: `${data.first_name} ${data.last_name}`,
                user_role: ROLES.DOCTOR,
                hospital_name: data.hospitals?.hospital_name_en,
                specialty: specialty,
                specialty_name: specialtyName
            };
        }
    },
    [ROLES.NURSE]: {
        table: 'nurses',
        select: 'id, first_name, last_name, user_id, hospital_id, hospitals(hospital_name_en)',
        transform: (data) => ({
            id: data.id,
            first_name: data.first_name,
            last_name: data.last_name,
            full_name: `${data.first_name} ${data.last_name}`,
            user_role: ROLES.NURSE,
            hospital_name: data.hospitals?.hospital_name_en
        })
    },
    [ROLES.ADMIN]: {
        table: 'administrators',
        select: 'id, first_name, last_name, user_id, hospital_id, hospitals(hospital_name_en)',
        transform: (data) => ({
            id: data.id,
            full_name: `${data.first_name} ${data.last_name}`,
            user_role: ROLES.ADMIN,
            hospital_name: data.hospitals?.hospital_name_en
        })
    },
    [ROLES.SUPER_ADMIN]: {
        table: 'administrators',
        select: 'id, first_name, last_name, user_id, hospital_id, hospitals(hospital_name_en)',
        transform: (data) => ({
            id: data.id,
            full_name: `${data.first_name} ${data.last_name}`,
            user_role: ROLES.SUPER_ADMIN,
            hospital_name: data.hospitals?.hospital_name_en
        })
    }
};

/**
 * Normalizes and validates role strings.
 * @param {string} role - The input role string.
 * @returns {string} - The standardized database role.
 * @throws {Error} - If role is invalid.
 */
export const normalizeRole = (role) => {
    if (!role) throw new Error('Role is required.');
    const normalized = ROLE_ALIAS_MAP[role.toLowerCase()];
    if (!normalized) throw new Error(`Invalid role specified: ${role}`);
    return normalized;
};

const isValidUUID = (str) =>
    typeof str === 'string' &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(str.trim());

/**
 * Constructs the standardized user_metadata payload for Supabase Auth.
 * Handles data normalization, validation, and role-specific requirements.
 * Used primarily for the SQL Trigger (basic info).
 */
export const createAuthPayload = (input) => {
    const role = normalizeRole(input.role);
    const firstName = (input.firstName || input.first_name || '').trim();
    const lastName = (input.lastName || input.last_name || '').trim();
    const fullName = (input.fullName || input.full_name || `${firstName} ${lastName}`).trim();

    if (fullName.length < 2) throw new Error("Full Name is invalid or too short.");

    // Base Metadata (Common to all roles)
    const metadata = {
        role: role,
        full_name: fullName,
        first_name: firstName || fullName.split(' ')[0],
        last_name: lastName || fullName.split(' ').slice(1).join(' '),
        phone: input.phone || null,
        country: input.country || input.countryId || null,
        region: input.region || input.regionId || null,
        city: input.city || null,
        address: input.address || null,
    };

    // Role-Specific Fields & Hospital Logic
    const hId = input.hospitalId || input.hospital_id;
    if ([ROLES.DOCTOR, ROLES.NURSE, ROLES.ADMIN, ROLES.SUPER_ADMIN].includes(role)) {
        if (isValidUUID(hId)) {
            metadata.hospital_id = hId;
            metadata.hospital_name = input.hospitalName || input.hospital_name || null;
        } else {
            // [DEFENSIVE] Avoid sending non-UUID placeholder strings ('biointellect-main-hq') to hospital_id column
            metadata.hospital_id = null;
            metadata.hospital_name = input.hospitalName || input.hospital_name || 'BioIntellect Medical Center';
        }
    } else if (role === ROLES.PATIENT) {
        if (isValidUUID(hId)) {
            metadata.hospital_id = hId;
        } else {
            metadata.hospital_id = null;
        }
    }

    // Pass basic specific fields to metadata for trigger safety
    if (role === ROLES.DOCTOR) {
        if (!input.licenseNumber && !input.license_number) throw new Error("License Number is required for Doctors.");
        metadata.license_number = input.licenseNumber || input.license_number;
    } else if (role === ROLES.NURSE) {
        metadata.nurse_title = input.nurseTitle || input.nurse_title || null;
    } else if (role === ROLES.PATIENT) {
        // [SECURITY] Force mandatory password reset for patients on first enrollment
        metadata.must_reset_password = true;
    }

    console.log("✅ [ROLES_CONFIG] Auth Payload Constructed:", metadata);
    return metadata;
};

/**
 * Constructs the full data object for the Database Update step.
 * Maps all form inputs to the exact column names in the schema.
 */
export const createProfileData = (input) => {
    const role = normalizeRole(input.role);
    console.log("🛠️ [ROLES_CONFIG] Constructing Profile Data for DB...", role);

    const common = {
        first_name: input.firstName || input.first_name,
        last_name: input.lastName || input.last_name,
        first_name_ar: input.firstNameAr || input.first_name_ar || null,
        last_name_ar: input.lastNameAr || input.last_name_ar || null,
        phone: input.phone || null,
        hospital_id: input.hospitalId || input.hospital_id || null, // [CRITICAL] Ensure hospital is linked
    };

    if (role === ROLES.PATIENT) {
        return {
            ...common,
            role: role, // [CRITICAL] Explicitly save role
            // Core
            date_of_birth: input.dateOfBirth || input.date_of_birth || null,
            gender: input.gender || 'male',
            blood_type: input.bloodType || input.blood_type || 'unknown',

            // ID Documents
            national_id: input.nationalId || input.national_id || null,
            passport_number: input.passportNumber || input.passport_number || null,

            // Address
            address: input.address || null,
            city: input.city || null,
            region_id: input.regionId || null,
            country_id: input.countryId || null,

            // Emergency
            emergency_contact_name: input.emergencyContactName || input.emergency_contact_name || null,
            emergency_contact_phone: input.emergencyContactPhone || input.emergency_contact_phone || null,
            emergency_contact_relation: input.emergencyContactRelation || input.emergency_contact_relation || null,

            // Medical History
            allergies: Array.isArray(input.allergies) ? input.allergies : [],
            chronic_conditions: Array.isArray(input.chronicConditions) ? input.chronicConditions : [],
            current_medications: Array.isArray(input.currentMedications) ? input.currentMedications : [],

            // Insurance
            insurance_provider: input.insuranceProvider || input.insurance_provider || null,
            insurance_number: input.insuranceNumber || input.insurance_number || null,

            // Text
            notes: input.notes || null,

            is_active: true
        };
    }

    if (role === ROLES.DOCTOR) {
        return {
            ...common,
            role: role, // [CRITICAL] Explicitly save role
            gender: input.gender || null,
            date_of_birth: input.dateOfBirth || null,

            license_number: input.licenseNumber || input.license_number,
            license_expiry: input.licenseExpiry || input.license_expiry || null,

            qualification: input.qualifications || null,
            years_of_experience: input.yearsOfExperience ? parseInt(input.yearsOfExperience) : 0,
            bio: input.bio || null,
            employee_id: input.employeeId || input.employee_id || null,

            is_active: true
        };
    }

    if (role === ROLES.NURSE) {
        return {
            ...common,
            role: role,
            gender: input.gender || null,
            date_of_birth: input.dateOfBirth || null,
            qualification: input.qualifications || null,
            years_of_experience: input.yearsOfExperience ? parseInt(input.yearsOfExperience) : 0,
            bio: input.bio || null,
            employee_id: input.employeeId || input.employee_id || null,
            nurse_title: input.nurseTitle || input.nurse_title || null,
            is_active: true
        };
    }

    if (role === ROLES.ADMIN || role === ROLES.SUPER_ADMIN) {
        return {
            ...common,
            role: role,
            department: input.department || null,
            employee_id: input.employeeId || input.employee_id || null,
            national_id: input.nationalId || input.national_id || null,
            is_active: true
        };
    }

    return {};
};
