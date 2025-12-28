import { z } from 'zod'

export const signupSchema = z.object({
    email: z.string().email('Invalid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    role: z.enum(['super_admin', 'admin', 'doctor', 'nurse', 'patient']),
    first_name: z.string().min(2, 'First name is required'),
    last_name: z.string().min(2, 'Last name is required'),
    gender: z.enum(['male', 'female']).optional(),
    date_of_birth: z.string().optional(),
    country_id: z.string().optional(),
    region_id: z.string().optional(),
    hospital_id: z.string().uuid('Invalid hospital ID').optional(),
    license_number: z.string().optional(),
}).refine((data) => {
    // Super Admin doesn't need hospital_id
    if (data.role === 'super_admin') return true

    // Admin, Doctor, Nurse MUST have hospital_id
    if (['admin', 'doctor', 'nurse'].includes(data.role)) {
        return !!data.hospital_id
    }

    return true
}, {
    message: 'Hospital ID is required for this role',
    path: ['hospital_id'],
}).refine((data) => {
    // Doctor MUST have license_number
    if (data.role === 'doctor') {
        return !!data.license_number
    }
    return true
}, {
    message: 'License number is required for doctors',
    path: ['license_number'],
})

export type SignupSchema = z.infer<typeof signupSchema>
