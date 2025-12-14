/**
 * API Service
 * 
 * Handle all API calls to Supabase
 * Authentication and Database operations
 */

import supabase from '../config/supabase'

/**
 * Authentication Service
 */
export const authService = {
  /**
   * Sign up with email and password
   */
  signUp: async (email, password, fullName) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName
          }
        }
      })

      if (error) throw error

      // Insert user data into users table
      const { error: insertError } = await supabase.from('users').insert([
        {
          id: data.user.id,
          email: data.user.email,
          full_name: fullName,
          user_role: 'patient',
          is_verified: false,
          is_active: true
        }
      ])

      if (insertError) throw insertError

      return { success: true, user: data.user }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  /**
   * Sign in with email and password
   */
  signIn: async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      })

      if (error) throw error

      // Get user data from users table
      const { data: userData, error: fetchError } = await supabase
        .from('users')
        .select('*')
        .eq('id', data.user.id)
        .single()

      if (fetchError) throw fetchError

      return { success: true, user: userData }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  /**
   * Sign out
   */
  signOut: async () => {
    try {
      const { error } = await supabase.auth.signOut()
      if (error) throw error
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  /**
   * Reset password
   */
  resetPassword: async (email) => {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`
      })

      if (error) throw error
      return { success: true }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  /**
   * Get current user
   */
  getCurrentUser: async () => {
    try {
      const {
        data: { user },
        error
      } = await supabase.auth.getUser()

      if (error) throw error
      return { success: true, user }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }
}

/**
 * Users Service
 */
export const usersService = {
  /**
   * Get user profile
   */
  getUserProfile: async (userId) => {
    try {
      const { data, error } = await supabase
        .from('users')
        .select('*')
        .eq('id', userId)
        .single()

      if (error) throw error
      return { success: true, data }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  /**
   * Update user profile
   */
  updateUserProfile: async (userId, updates) => {
    try {
      const { data, error } = await supabase
        .from('users')
        .update(updates)
        .eq('id', userId)
        .select()
        .single()

      if (error) throw error
      return { success: true, data }
    } catch (error) {
      return { success: false, error: error.message }
    }
  },

  /**
   * Update user role
   */
  updateUserRole: async (userId, role) => {
    try {
      const { data, error } = await supabase
        .from('users')
        .update({ user_role: role })
        .eq('id', userId)
        .select()
        .single()

      if (error) throw error
      return { success: true, data }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }
}

export default {
  authService,
  usersService
}
