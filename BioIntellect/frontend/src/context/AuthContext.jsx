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

  const signUp = async (signUpData) => {
    setIsLoading(true)
    setError(null)

    // Destructure new data format
    const { email, password, firstName, lastName, role, dateOfBirth, gender } = signUpData
    const full_name = firstName && lastName ? `${firstName} ${lastName}` : signUpData.full_name

    try {
      // Check if Supabase is configured
      if (!supabase || !import.meta.env.VITE_SUPABASE_URL) {
        // Fallback to mock
        await wait()
        const users = loadMockUsers()
        const exists = users.find((u) => u.email === email)
        if (exists) {
          setError('Email already registered')
          setIsLoading(false)
          return { success: false, error: 'Email already registered' }
        }

        const newUser = {
          user_id: `mock_${Date.now()}`,
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

        setIsLoading(false)
        return { success: true, user: newUser }
      }

      // 1. Create Supabase Auth User
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
        setIsLoading(false)
        return { success: false, error: authError.message }
      }

      if (!authData.user) {
        setError('Registration failed. Please try again.')
        setIsLoading(false)
        return { success: false, error: 'User creation failed' }
      }

      // 2. Insert into public.users (Common for all roles)
      const { error: profileError } = await supabase.from('users').insert({
        user_id: authData.user.id,
        email: email,
        full_name: full_name,
        password_hash: 'SUPABASE_AUTH_MANAGED', // Placeholder
        user_role: role, // Specific role (e.g. 'cardiologist', 'patient')
        is_active: true,
        is_verified: false,
        phone_number: null,
      })

      if (profileError) {
        console.error('User Profile Error:', profileError)
        setError(profileError.message)
        setIsLoading(false)
        return { success: false, error: profileError.message }
      }

      // 3. If Patient, Insert into public.patients
      if (role === 'patient') {
        const mrn = `MRN-${Date.now().toString().slice(-8)}-${Math.floor(Math.random() * 1000)}`

        const { error: patientError } = await supabase.from('patients').insert({
          medical_record_number: mrn,
          first_name: firstName,
          last_name: lastName,
          date_of_birth: dateOfBirth,
          gender: gender,
          email: email,
          created_by: authData.user.id,
          is_active: true
        })

        if (patientError) {
          console.error('Patient Profile Error:', patientError)
          setError(`User created but patient profile failed: ${patientError.message}`)
          setIsLoading(false)
          return { success: false, error: patientError.message }
        }
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

      setIsLoading(false)
      return { success: true, user: newUser }
    } catch (err) {
      console.error('SignUp Exception:', err)
      setError(err.message)
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

          setIsLoading(false)
          return { success: false, error: 'Invalid credentials' }
        }

        localStorage.setItem('biointellect_current_user', JSON.stringify(found))
        setCurrentUser(found)
        setIsAuthenticated(true)
        setUserRole(found.user_role)
        localStorage.setItem('userRole', found.user_role)

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

        setIsLoading(false)
        return { success: false, error: authError.message }
      }

      // Get user profile
      let { data: userData, error: profileError } = await supabase
        .from('users')
        .select('*')
        .eq('user_id', authData.user.id)
        .maybeSingle() // Use maybeSingle to avoid 'JSON object' error if 0 rows

      // If profile is missing (orphaned auth user), try to recover/create it
      if (!userData) {
        console.warn('User profile missing, attempting recovery...')
        const recoveryData = {
          user_id: authData.user.id,
          email: email,
          full_name: authData.user.user_metadata?.full_name || 'User',
          password_hash: 'SUPABASE_AUTH_MANAGED',
          user_role: authData.user.user_metadata?.user_role || 'doctor', // Default fallback
          is_active: true,
          is_verified: false, // Default to unverified
        }

        const { data: newProfile, error: recoveryError } = await supabase
          .from('users')
          .upsert(recoveryData, { onConflict: 'user_id' }) // Use Upsert to fix duplicate key error
          .select()
          .single()

        if (recoveryError) {
          setError('Profile recovery failed: ' + recoveryError.message)
          setIsLoading(false)
          return { success: false, error: recoveryError.message }
        }
        userData = newProfile
      }
      else if (profileError) {
        setError(profileError.message)
        setIsLoading(false)
        return { success: false, error: profileError.message }
      }

      localStorage.setItem('biointellect_current_user', JSON.stringify(userData))
      setCurrentUser(userData)
      setIsAuthenticated(true)
      setUserRole(userData.user_role)
      localStorage.setItem('userRole', userData.user_role)

      setIsLoading(false)
      return { success: true, user: userData }
    } catch (err) {
      setError(err.message)

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

          setIsLoading(false)
          return { success: false, error: 'Email not found' }
        }
        // The following lines were removed as they were syntactically incorrect and likely unintended JSX.
        // The original intent was likely to remove the `found.is_verified = true` and `saveMockUsers(users)`
        // as a password reset in a mock scenario should not modify user data directly.

        // found.is_verified = true // Removed
        // saveMockUsers(users) // Removed

        setIsLoading(false)
        return { success: true }
      }

      // Use Supabase
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      })

      if (error) {
        setError(error.message)

        setIsLoading(false)
        return { success: false, error: error.message }
      }


      setIsLoading(false)
      return { success: true }
    } catch (err) {
      setError(err.message)

      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }

  // Function for Admins to register patients without losing their own session
  const registerPatient = async (patientData) => {
    // We utilize a separate client instance or just the API to avoid auth context switching if possible.
    // However, Supabase JS client auth is singleton by default in the browser.
    // To work around this without a backend, we can use the `supabase.auth.admin.createUser` ONLY if we are in a service role context (Backend).
    // BUT we are on frontend. 
    // The standard workaround for frontend "Admin creates User" without logout is:
    // 1. We cannot strictly do this securely purely on frontend without logging out the admin, UNLESS we use a second `createClient` instance with memory storage.

    try {
      // Import createClient dynamically or use the one from supabase-js
      const { createClient } = await import('@supabase/supabase-js')

      const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
      const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY

      // Create a temporary client with memory storage so it doesn't persist/override local storage
      const tempSupabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
        auth: {
          storage: {
            getItem: () => null,
            setItem: () => { },
            removeItem: () => { },
          },
          persistSession: false,
          autoRefreshToken: false,
          detectSessionInUrl: false
        }
      })

      const { email, password, firstName, lastName, dateOfBirth, gender, phone, address } = patientData
      const full_name = `${firstName} ${lastName}`

      // 1. Create User via Temp Client
      const { data: authData, error: authError } = await tempSupabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name,
            user_role: 'patient',
          }
        }
      })

      if (authError) throw authError
      if (!authData.user) throw new Error('Failed to create user')

      // 2. Main Admin Client performs database inserts (RLS should allow Admin to insert)

      // 2. Call the Secure Database Function (RPC) to create profiles
      // This bypasses RLS issues because the function runs as Security Definer
      const { data: mrn, error: rpcError } = await supabase.rpc('register_patient_profile', {
        p_user_id: authData.user.id,
        p_email: email,
        p_first_name: firstName,
        p_last_name: lastName,
        p_full_name: full_name,
        p_dob: dateOfBirth,
        p_gender: gender,
        p_phone: phone || null,
        p_address: address || null
      })

      if (rpcError) throw rpcError

      return { success: true, user: authData.user, mrn }

    } catch (error) {
      console.error('Register Patient Error:', error)
      return { success: false, error: error.message }
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
    registerPatient,
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
