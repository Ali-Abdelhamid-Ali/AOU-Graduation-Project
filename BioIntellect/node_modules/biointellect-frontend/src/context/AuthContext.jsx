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

  // ============================================================================
  // Session Timeout Logic (15 Minutes)
  // ============================================================================
  useEffect(() => {
    if (!isAuthenticated) return

    const TIMEOUT_MS = 15 * 60 * 1000 // 15 minutes
    const CHECK_INTERVAL = 60 * 1000 // Check every minute

    const updateActivity = () => {
      localStorage.setItem('biointellect_last_activity', Date.now().toString())
    }

    const checkInactivity = () => {
      const lastActivity = parseInt(localStorage.getItem('biointellect_last_activity') || '0', 10)
      if (Date.now() - lastActivity > TIMEOUT_MS) {
        signOut() // Auto-logout
      }
    }

    // Initialize activity timestamp on mount/login if not present
    if (!localStorage.getItem('biointellect_last_activity')) {
      updateActivity()
    }

    // Listeners for user activity
    window.addEventListener('mousemove', updateActivity)
    window.addEventListener('keydown', updateActivity)
    window.addEventListener('click', updateActivity)
    window.addEventListener('scroll', updateActivity)

    // Interval to check timeout
    const intervalId = setInterval(checkInactivity, CHECK_INTERVAL)

    return () => {
      window.removeEventListener('mousemove', updateActivity)
      window.removeEventListener('keydown', updateActivity)
      window.removeEventListener('click', updateActivity)
      window.removeEventListener('scroll', updateActivity)
      clearInterval(intervalId)
    }
  }, [isAuthenticated])

  const selectRole = (role) => {
    if (!['doctor', 'patient'].includes(role)) {
      setError('Invalid role')
      return
    }
    setUserRole(role)
    localStorage.setItem('userRole', role)
    setError(null)
  }

  // Helper to hash password using SHA-256 (Web Crypto API)
  const hashPassword = async (password) => {
    if (!password) return null;
    const msgUint8 = new TextEncoder().encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgUint8);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
  };

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

        const hashedPassword = await hashPassword(password)
        const newUser = {
          user_id: `mock_${Date.now()}`,
          email,
          full_name,
          password_hash: hashedPassword, // Mocking the hash field
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
          emailRedirectTo: `${window.location.origin}/`,
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

      // 2. Insert into users table (Common Record)
      // 2. Insert into users table (Common Record)
      const { error: profileError } = await supabase.from('users').insert({
        user_id: authData.user.id,
        email: email,
        password_hash: 'SUPABASE_AUTH_MANAGED',
        full_name: full_name,
        user_role: role,
        is_active: true,
        is_verified: true,
        email_verified_at: new Date().toISOString()
      })

      if (profileError) throw profileError

      // 3. Insert into Role-Specific Table
      if (role === 'patient') {
        const { error: patientError } = await supabase.from('patients').insert({
          patient_id: authData.user.id,
          first_name: firstName,
          last_name: lastName,
          date_of_birth: dateOfBirth,
          gender: gender || 'male',
          email: email,
          is_active: true,
          consent_given: true,
          consent_date: new Date().toISOString()
        })

        if (patientError) throw patientError
      }

      const newUser = {
        user_id: authData.user.id,
        email,
        full_name,
        user_role: role,
        is_verified: true,
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
        const hashedInput = await hashPassword(password)
        const found = users.find((u) => u.email === email && (u.password_hash === hashedInput || u.password === password))
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

      // 2. Resolve Profile - Direct lookup in the appropriate table based on role
      const userRoleFromAuth = authData.user.user_metadata?.user_role

      // Enforce Role Consistency:
      // - If user is on the Patient path, they MUST have a 'patient' account.
      // - If user is on the Doctor/Medical path, any non-patient account (Admin, Physician, etc.) is allowed.
      if (userRole === 'patient' && userRoleFromAuth !== 'patient') {
        await supabase.auth.signOut()
        setError('Access Denied: This login portal is restricted to patients only.')
        setIsLoading(false)
        return { success: false, error: 'Role mismatch' }
      }

      if (userRole === 'doctor' && userRoleFromAuth === 'patient') {
        await supabase.auth.signOut()
        setError('Access Denied: Patients cannot access the medical staff portal.')
        setIsLoading(false)
        return { success: false, error: 'Role mismatch' }
      }

      let userData = null

      if (userRoleFromAuth === 'patient') {
        // High-Priority Patient Verification: Check the 'patients' table ONLY
        const { data: patientData, error: patientError } = await supabase
          .from('patients')
          .select('*')
          .eq('patient_id', authData.user.id)
          .maybeSingle()

        if (patientError) throw patientError

        if (!patientData) {
          await supabase.auth.signOut()
          setError('Security Breach: Patient profile missing in clinical records.')
          setIsLoading(false)
          return { success: false, error: 'Patient profile missing' }
        }

        userData = {
          ...patientData,
          id: authData.user.id,
          full_name: `${patientData.first_name} ${patientData.last_name}`,
          user_role: 'patient'
        }
      } else {
        // Staff/Admin lookup in the 'users' table
        const { data: staffData, error: staffError } = await supabase
          .from('users')
          .select('*')
          .eq('user_id', authData.user.id)
          .maybeSingle()

        if (staffError) throw staffError

        if (!staffData) {
          await supabase.auth.signOut()
          setError('Staff profile record not found.')
          setIsLoading(false)
          return { success: false, error: 'User profile missing' }
        }
        userData = staffData
      }

      localStorage.setItem('biointellect_current_user', JSON.stringify(userData))
      setCurrentUser(userData)
      setIsAuthenticated(true)
      setUserRole(userData.user_role)
      localStorage.setItem('userRole', userData.user_role)

      setIsLoading(false)
      return { success: true, user: userData, role: userData.user_role }
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

        setIsLoading(false)
        return { success: true }
      }

      // Use Supabase
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}`,
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

  const updatePassword = async (newPassword) => {
    setIsLoading(true)
    setError(null)

    try {
      if (!supabase || !import.meta.env.VITE_SUPABASE_URL) {
        await wait()
        // Mock update
        setIsLoading(false)
        return { success: true }
      }

      const { data, error } = await supabase.auth.updateUser({
        password: newPassword
      })

      if (error) {
        setError(error.message)
        setIsLoading(false)
        return { success: false, error: error.message }
      }


      setIsLoading(false)
      return { success: true, user: data.user }
    } catch (err) {
      setError(err.message)
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }

  // Function for Admins to register patients without losing their own session
  const registerDoctor = async (doctorData) => {
    setIsLoading(true)
    setError(null)
    try {
      const { createClient } = await import('@supabase/supabase-js')
      const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
      const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY

      const tempSupabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
        auth: {
          storage: { getItem: () => null, setItem: () => { }, removeItem: () => { } },
          persistSession: false,
          autoRefreshToken: false,
          detectSessionInUrl: false
        }
      })

      const { email, password, fullName, specialty, phone, licenseNumber } = doctorData

      // 1. Create Auth User
      const { data: authData, error: authError } = await tempSupabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
            user_role: specialty || 'physician',
          }
        }
      })

      if (authError) throw authError
      if (!authData.user) throw new Error('Failed to create auth user')

      // 2. Create Profile in public.users - EXACT MATCH TO PROVIDED SCHEMA
      const { error: profileError } = await supabase.from('users').insert({
        user_id: authData.user.id,
        email: email,
        password_hash: 'SUPABASE_AUTH_MANAGED',
        full_name: fullName,
        phone_number: phone || null,
        user_role: specialty || 'physician',
        specialty: specialty || 'General Medicine', // Filling specialty column
        license_number: licenseNumber || null,
        is_active: true,
        is_verified: true,
        email_verified_at: new Date().toISOString()
      })

      if (profileError) throw profileError

      setIsLoading(false)
      return { success: true, user: authData.user }
    } catch (err) {
      console.error('Register Doctor Error:', err)
      setError(err.message)
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }
  const registerPatient = async (patientData) => {
    try {
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

      const {
        email,
        password,
        firstName,
        lastName,
        dateOfBirth,
        gender,
        phone,
        address,
        city,
        country,
        bloodType,
        allergies,
        chronicConditions,
        emergencyContactName,
        emergencyContactPhone,
        emergencyContactRelation,
        currentMedications,
        consentGiven,
        dataRetentionUntil
      } = patientData
      const full_name = `${firstName} ${lastName}`

      // 1. Create User via Temp Client (to handle Supabase Auth without logging out Admin)
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

      // 2. Create User Profile in public.users (Schema requirement: Patients MUST have a user record for FK/Role checks)
      const { error: userError } = await supabase.from('users').insert({
        user_id: authData.user.id,
        email: email,
        password_hash: 'SUPABASE_AUTH_MANAGED',
        full_name: full_name,
        user_role: 'patient',
        is_active: true,
        is_verified: true,
        email_verified_at: new Date().toISOString()
      })

      if (userError) throw userError

      // 3. Create Patient Record (Matching EXACT provided schema)
      // MRN is now handled by database trigger trigger_generate_mrn
      const { data: patientRecord, error: patientError } = await supabase.from('patients').insert({
        patient_id: authData.user.id, // Linking patient_id directly to auth user id
        first_name: firstName,
        last_name: lastName,
        date_of_birth: dateOfBirth,
        gender: gender || 'male',
        blood_type: bloodType || null,
        phone_number: phone || null,
        email: email || null,
        address: address || null,
        city: city || null,
        country: country || 'Egypt',
        emergency_contact_name: emergencyContactName || null,
        emergency_contact_phone: emergencyContactPhone || null,
        emergency_contact_relation: emergencyContactRelation || null,
        allergies: allergies || [],
        chronic_conditions: chronicConditions || [],
        current_medications: currentMedications || {},
        created_by: currentUser?.user_id || currentUser?.id, // Admin who created this
        is_active: true,
        consent_given: consentGiven || false,
        consent_date: consentGiven ? new Date().toISOString() : null,
        data_retention_until: dataRetentionUntil || null
      }).select().single()

      if (patientError) throw patientError

      return {
        success: true,
        user: authData.user,
        mrn: patientRecord.medical_record_number,
        patient_id: patientRecord.patient_id,
        user_id: authData.user.id
      }

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
    updatePassword,
    registerPatient,
    registerDoctor,
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
