import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../config/supabase'

/**
 * Mock AuthContext
 *
 * This provider implements a mock authentication flow (no Supabase, no API calls),
 * designed to match the Supabase schema names so the UI can be connected later.
 *
 * Exports:
 * - `signUp(full_name, email, password, role)`
 * - `signIn(email, password)`
 * - `signOut()`
 * - `resetPassword(email)`
 * - `selectRole(role)`
 * - `clearError()`
 *
 * All functions are async (return a Promise) and simulate network latency.
 */

const AuthContext = createContext()

const MOCK_USERS_KEY = 'biointellect_mock_users'

const loadMockUsers = () => {
  try {
    const raw = localStorage.getItem(MOCK_USERS_KEY)
    return raw ? JSON.parse(raw) : []
  } catch (e) {
    return []
  }
}

const saveMockUsers = (users) => {
  localStorage.setItem(MOCK_USERS_KEY, JSON.stringify(users))
}

export const AuthProvider = ({ children }) => {
  const [userRole, setUserRole] = useState(() => localStorage.getItem('userRole') || null)
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!localStorage.getItem('biointellect_current_user'))
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const u = localStorage.getItem('biointellect_current_user')
      return u ? JSON.parse(u) : null
    } catch (e) {
      return null
    }
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Toast function - will be injected by ToastProvider wrapper
  const [toastFn, setToastFn] = useState(null)
  
  const showToast = (message, type = 'success') => {
    if (toastFn) {
      toastFn(message, type)
    } else {
      console.log(`[${type.toUpperCase()}] ${message}`)
    }
  }
  
  // Expose setToastFn for ToastProvider to inject
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.__setAuthToast = setToastFn
    }
  }, [])

  useEffect(() => {
    if (currentUser && currentUser.user_role) setUserRole(currentUser.user_role)
  }, [currentUser])

  const selectRole = (role) => {
    if (!['doctor', 'patient'].includes(role)) {
      setError('Invalid role')
      return
    }
    setUserRole(role)
    localStorage.setItem('userRole', role)
    setError(null)
  }

  // Helper to simulate latency
  const wait = (ms = 400) => new Promise((res) => setTimeout(res, ms))

  const signUp = async (full_name, email, password, role = 'patient') => {
    setIsLoading(true)
    setError(null)

    try {
      // Check if Supabase is configured
      if (!supabase || !import.meta.env.VITE_SUPABASE_URL) {
        // Fallback to mock
        await wait()
        const users = loadMockUsers()
        const exists = users.find((u) => u.email === email)
        if (exists) {
          setError('Email already registered')
          showToast?.('Email already registered', 'error')
          setIsLoading(false)
          return { success: false, error: 'Email already registered' }
        }

        const newUser = {
          id: `mock_${Date.now()}`,
          email,
          full_name,
          password,
          user_role: role,
          is_active: true,
          is_verified: false,
        }

        users.push(newUser)
        saveMockUsers(users)
        localStorage.setItem('biointellect_current_user', JSON.stringify(newUser))
        setCurrentUser(newUser)
        setIsAuthenticated(true)
        setUserRole(role)
        localStorage.setItem('userRole', role)
        showToast?.('Account created successfully!', 'success')
        setIsLoading(false)
        return { success: true, user: newUser }
      }

      // Use Supabase
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name,
            user_role: role,
          },
        },
      })

      if (authError) {
        setError(authError.message)
        showToast?.(authError.message, 'error')
        setIsLoading(false)
        return { success: false, error: authError.message }
      }

      // Create user profile in users table
      const { error: profileError } = await supabase.from('users').insert({
        id: authData.user.id,
        email,
        full_name,
        user_role: role,
        is_verified: false,
        is_active: true,
      })

      if (profileError) {
        setError(profileError.message)
        showToast?.(profileError.message, 'error')
        setIsLoading(false)
        return { success: false, error: profileError.message }
      }

      const newUser = {
        id: authData.user.id,
        email,
        full_name,
        user_role: role,
        is_verified: false,
        is_active: true,
      }

      localStorage.setItem('biointellect_current_user', JSON.stringify(newUser))
      setCurrentUser(newUser)
      setIsAuthenticated(true)
      setUserRole(role)
      localStorage.setItem('userRole', role)
      showToast?.('Account created successfully!', 'success')
      setIsLoading(false)
      return { success: true, user: newUser }
    } catch (err) {
      setError(err.message)
      showToast?.(err.message, 'error')
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }

  const signIn = async (email, password) => {
    setIsLoading(true)
    setError(null)

    try {
      // Check if Supabase is configured
      if (!supabase || !import.meta.env.VITE_SUPABASE_URL) {
        // Fallback to mock
        await wait()
        const users = loadMockUsers()
        const found = users.find((u) => u.email === email && u.password === password)
        if (!found) {
          setError('Invalid credentials')
          showToast?.('Invalid email or password', 'error')
          setIsLoading(false)
          return { success: false, error: 'Invalid credentials' }
        }

        localStorage.setItem('biointellect_current_user', JSON.stringify(found))
        setCurrentUser(found)
        setIsAuthenticated(true)
        setUserRole(found.user_role)
        localStorage.setItem('userRole', found.user_role)
        showToast?.('Signed in successfully!', 'success')
        setIsLoading(false)
        return { success: true, user: found }
      }

      // Use Supabase
      const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (authError) {
        setError(authError.message)
        showToast?.(authError.message, 'error')
        setIsLoading(false)
        return { success: false, error: authError.message }
      }

      // Get user profile
      const { data: userData, error: profileError } = await supabase
        .from('users')
        .select('*')
        .eq('id', authData.user.id)
        .single()

      if (profileError) {
        setError(profileError.message)
        showToast?.(profileError.message, 'error')
        setIsLoading(false)
        return { success: false, error: profileError.message }
      }

      localStorage.setItem('biointellect_current_user', JSON.stringify(userData))
      setCurrentUser(userData)
      setIsAuthenticated(true)
      setUserRole(userData.user_role)
      localStorage.setItem('userRole', userData.user_role)
      showToast?.('Signed in successfully!', 'success')
      setIsLoading(false)
      return { success: true, user: userData }
    } catch (err) {
      setError(err.message)
      showToast?.(err.message, 'error')
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }

  const signOut = async () => {
    setIsLoading(true)

    try {
      if (supabase && import.meta.env.VITE_SUPABASE_URL) {
        await supabase.auth.signOut()
      }
      
      localStorage.removeItem('biointellect_current_user')
      setCurrentUser(null)
      setIsAuthenticated(false)
      setUserRole(null)
      localStorage.removeItem('userRole')
      showToast?.('Signed out successfully', 'info')
      setIsLoading(false)
      return { success: true }
    } catch (err) {
      setError(err.message)
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }

  const resetPassword = async (email) => {
    setIsLoading(true)
    setError(null)

    try {
      // Check if Supabase is configured
      if (!supabase || !import.meta.env.VITE_SUPABASE_URL) {
        // Fallback to mock
        await wait()
        const users = loadMockUsers()
        const found = users.find((u) => u.email === email)
        if (!found) {
          setError('Email not found')
          showToast?.('Email not found', 'error')
          setIsLoading(false)
          return { success: false, error: 'Email not found' }
        }

        found.is_verified = true
        saveMockUsers(users)
        showToast?.('Password reset email sent!', 'success')
        setIsLoading(false)
        return { success: true }
      }

      // Use Supabase
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      })

      if (error) {
        setError(error.message)
        showToast?.(error.message, 'error')
        setIsLoading(false)
        return { success: false, error: error.message }
      }

      showToast?.('Password reset email sent! Check your inbox.', 'success')
      setIsLoading(false)
      return { success: true }
    } catch (err) {
      setError(err.message)
      showToast?.(err.message, 'error')
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }

  const clearError = () => setError(null)

  const value = {
    userRole,
    currentUser,
    isAuthenticated,
    isLoading,
    error,

    // Actions
    selectRole,
    signUp,
    signIn,
    signOut,
    resetPassword,
    clearError,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// ============================================================================
// Custom Hook to use Auth Context
// ============================================================================
export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export default AuthContext
