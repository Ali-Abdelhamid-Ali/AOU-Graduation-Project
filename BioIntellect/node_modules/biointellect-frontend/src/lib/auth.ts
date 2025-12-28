import { supabase } from '../config/supabase'
import { SignupFormData, AuthResponse } from '../types/auth.types'

/**
 * Enhanced Signup Function
 * Corrects metadata structure for Supabase trigger
 */
export const signUp = async (formData: SignupFormData): Promise<AuthResponse> => {
    try {
        const { email, password, role, hospital_id, first_name, last_name, license_number } = formData

        // Build metadata object exactly as expected by the trigger
        const metadata: Record<string, any> = {
            role,
            first_name,
            last_name,
            full_name: `${first_name} ${last_name}`.trim(),
        }

        // Conditional metadata
        if (hospital_id && role !== 'super_admin') {
            metadata.hospital_id = hospital_id
        }

        if (role === 'doctor' && license_number) {
            metadata.license_number = license_number
        }

        console.log('🚀 [AUTH] Registering user with metadata:', metadata)

        const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: metadata, // This goes to raw_user_meta_data
                emailRedirectTo: `${window.location.origin}/auth/callback`,
            },
        })

        if (error) {
            console.error('❌ [AUTH] Signup Error:', error.message)
            return { success: false, error: error.message }
        }

        return { success: true, user: data.user }
    } catch (err: any) {
        console.error('💥 [AUTH] Unexpected Error:', err)
        return { success: false, error: err.message || 'An unexpected error occurred' }
    }
}
