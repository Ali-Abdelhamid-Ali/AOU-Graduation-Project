
import { createClient } from '@supabase/supabase-js'

// Environment variables
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY

// Validate environment variables
if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.error(
    'Missing Supabase environment variables. Please check .env.local file.'
  )
}

// Create Supabase client
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

/**
 * React equivalent to Next.js getServerComponentClient logic
 * Fetches the currently authenticated user from Supabase.
 */
export const getCurrentUser = async () => {
  try {
    const { data: { user }, error } = await supabase.auth.getUser()
    if (error) throw error
    return { data: user, error: null }
  } catch (error) {
    console.error('🔑 Auth Error:', error.message)
    return { data: null, error }
  }
}

/**
 * Diagnostic tool to verify database connectivity.
 * Aligned with 2024 SQL Schema.
 */
export const testSupabaseConnection = async () => {
  try {
    const { error } = await supabase.from('countries').select('id', { head: true, count: 'exact' }).limit(1)
    if (error) throw error
    console.log('🛡️ [SYSTEM]: Clinical Database Connection Verified.')
  } catch (err) {
    console.error('🚨 [CRITICAL]: Database Connection Failed:', err.message)
  }
}

export default supabase
