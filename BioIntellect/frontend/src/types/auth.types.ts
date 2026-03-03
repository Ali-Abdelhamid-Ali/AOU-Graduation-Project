export type UserRole = 'super_admin' | 'admin' | 'doctor' | 'nurse' | 'patient'

export interface SignupFormData {
    email: string
    password: string
    role: UserRole
    hospital_id?: string
    first_name: string
    last_name: string
    license_number?: string // for doctors
    gender?: 'male' | 'female'
    date_of_birth?: string
}

export interface AuthResponse {
    success: boolean
    user?: any
    error?: string
}
