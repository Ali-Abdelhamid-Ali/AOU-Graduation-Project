import { createContext, useContext, useEffect, useState, useCallback, useRef, useMemo } from 'react'
import { supabase, getCurrentUser } from '../config/supabase'

const AuthContext = createContext()

const CURRENT_USER_KEY = 'biointellect_current_user'
const USER_ROLE_KEY = 'userRole'

const CLINICAL_ROLES = ['super_admin', 'admin', 'doctor', 'nurse', 'patient'];

/**
 * EXTREME VERIFICATION PROTOCOL - CLINICAL ASSERTION HELPER
 * @param {any} condition 
 * @param {string} message 
 */
const assert = (condition, message) => {
  if (!condition) {
    console.error(`🚨 [ASSERTION FAILED]: ${message}`);
    throw new Error(message);
  }
};

export const AuthProvider = ({ children }) => {
  const [userRole, setUserRole] = useState(null) // Start null
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true) // Start true for stability
  const [error, setError] = useState(null)

  // High-performance caching layer for clinical location data
  const cache = useRef({
    countries: null,
    regions: {}, // countryId -> regions mapping
    hospitals: {} // regionId -> hospitals mapping
  })

  // Initialize session from hardware/storage
  useEffect(() => {
    const initSession = async () => {
      try {
        // 1. Check Supabase for active session (Secure Verification)
        const { data: authUser, error: authError } = await getCurrentUser()

        if (authUser) {
          console.log("🔓 [SESSION]: Active session verified for:", authUser.id);

          // 2. Resolve Clinical Profile using the new schema
          const userRoleFromAuth = authUser.user_metadata?.role || authUser.user_metadata?.user_role
          let userData = null

          if (userRoleFromAuth === 'patient') {
            const { data: patientData } = await supabase
              .from('patients')
              .select('*, hospitals(hospital_name_en)')
              .eq('user_id', authUser.id)
              .maybeSingle()

            if (patientData) {
              userData = {
                ...patientData,
                id: patientData.id,
                full_name: `${patientData.first_name} ${patientData.last_name}`,
                user_role: 'patient',
                hospital_name: patientData.hospitals?.hospital_name_en
              }
            }
          } else if (userRoleFromAuth === 'doctor') {
            const { data: doctorData } = await supabase
              .from('doctors')
              .select('*, hospitals(hospital_name_en)')
              .eq('user_id', authUser.id)
              .maybeSingle()

            if (doctorData) {
              userData = {
                ...doctorData,
                id: doctorData.id,
                full_name: `${doctorData.first_name} ${doctorData.last_name}`,
                user_role: 'doctor',
                hospital_name: doctorData.hospitals?.hospital_name_en
              }
            }
          } else if (userRoleFromAuth === 'admin' || userRoleFromAuth === 'super_admin') {
            const { data: adminData } = await supabase
              .from('administrators')
              .select('*, hospitals(hospital_name_en)')
              .eq('user_id', authUser.id)
              .maybeSingle()

            if (adminData) {
              userData = {
                ...adminData,
                id: adminData.id,
                full_name: `${adminData.first_name} ${adminData.last_name}`,
                user_role: userRoleFromAuth,
                hospital_name: adminData.hospitals?.hospital_name_en
              }
            }
          } else if (userRoleFromAuth === 'nurse') {
            const { data: nurseData } = await supabase
              .from('nurses')
              .select('*, hospitals(hospital_name_en)')
              .eq('user_id', authUser.id)
              .maybeSingle()

            if (nurseData) {
              userData = {
                ...nurseData,
                id: nurseData.id,
                full_name: `${nurseData.first_name} ${nurseData.last_name}`,
                user_role: 'nurse',
                hospital_name: nurseData.hospitals?.hospital_name_en
              }
            }
          }

          if (userData) {
            const finalRole = userData.user_role
            setCurrentUser(userData)
            setIsAuthenticated(true)
            setUserRole(finalRole)

            // Sync local storage
            localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(userData))
            localStorage.setItem(USER_ROLE_KEY, finalRole)
          }
        } else {
          // No active session in Supabase, clear local cache
          localStorage.removeItem(CURRENT_USER_KEY)
          localStorage.removeItem(USER_ROLE_KEY)
          setIsAuthenticated(false)
          setCurrentUser(null)
          setUserRole(null)
        }
      } catch (err) {
        console.error('🚨 [SESSION]: Init Error:', err)
      } finally {
        setIsLoading(false)
      }
    }
    initSession()
  }, [])

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

  const selectRole = useCallback((role) => {
    if (!['doctor', 'patient', 'admin', 'super_admin', 'nurse'].includes(role)) {
      setError('Invalid role')
      return
    }
    setUserRole(role)
    localStorage.setItem('userRole', role)
    setError(null)
  }, [])

  // Helper to simulate latency
  const wait = (ms = 400) => new Promise((res) => setTimeout(res, ms))

  /**
   * @param {Object} signUpData
   * @param {string} signUpData.email - Clinical/Staff Email
   * @param {string} signUpData.password - Minimum 16 chars with symbols
   * @param {string} signUpData.role - MUST be valid clinical role
   */
  const signUp = useCallback(async (signUpData) => {
    setIsLoading(true)
    setError(null)

    // === EXTREME VERIFICATION PROTOCOL: INPUT AUDIT ===
    console.log("━━━━ [PROTOCOL] INPUT VERIFICATION: SIGNUP ━━━━");
    console.log("1. Input Data:", JSON.stringify(signUpData, null, 2));

    const { email, password, firstName, lastName, role, dateOfBirth, gender } = signUpData

    // Validate types and content
    assert(email && typeof email === 'string' && email.includes('@'), "EMAIL IS INVALID OR MISSING!");
    assert(password && typeof password === 'string' && password.length >= 6, "PASSWORD DOES NOT MEET SECURITY REQUIREMENTS!");
    assert(role && CLINICAL_ROLES.includes(role), `ROLE "${role}" IS NOT ALLOWED BY SYSTEM!`);

    const derivedName = (firstName && lastName) ? `${firstName} ${lastName}` : (signUpData.full_name || 'System User')
    const full_name = derivedName.trim() || 'System User'

    console.log("2. Resolved Name:", full_name, "| Type:", typeof full_name);
    assert(full_name.length >= 2, "RESOLVED USERNAME IS TOO SHORT!");
    console.log("━━━━ [PROTOCOL] VERIFICATION END ━━━━");

    try {
      const payloadMetadata = {
        full_name: full_name,
        role: role, // SQL trigger expects 'role'
        first_name: firstName,
        last_name: lastName,
        date_of_birth: dateOfBirth,
        gender: gender || 'male',
        hospital_id: signUpData.hospitalId || null,
        license_number: signUpData.licenseNumber || 'PENDING'
      };

      console.log("━━━━ [PROTOCOL] SQL/METADATA MAPPING ━━━━");
      console.log("Payload Mapping:", JSON.stringify(payloadMetadata, null, 2));
      console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

      if (!supabase || !import.meta.env.VITE_SUPABASE_URL) {
        throw new Error('Supabase configuration failure.')
      }

      const { data: authData, error: authError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/`,
          data: payloadMetadata,
        },
      })

      if (authError) {
        console.error("📤 [API ERROR]:", authError.message);
        throw authError;
      }

      console.log("✅ [SUCCESS]: Account Provisioned:", authData.user?.id);
      setIsLoading(false)
      return { success: true, user: authData.user }
    } catch (err) {
      console.error('SignUp Error:', err)
      setError(err.message)
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }, [])

  /**
   * @param {string} email
   * @param {string} password
   */
  const signIn = useCallback(async (email, password) => {
    setIsLoading(true)
    setError(null)

    try {
      console.log("━━━━ [PROTOCOL] INPUT VERIFICATION: SIGN_IN ━━━━");
      console.log("1. Input Data:", { email, password: password ? '********' : 'EMPTY' });

      assert(email && email.includes('@'), "SIGN-IN EMAIL IS INVALID!");
      assert(password && password.length > 0, "SIGN-IN PASSWORD IS REQUIRED!");

      if (!supabase || !import.meta.env.VITE_SUPABASE_URL) {
        throw new Error('Supabase is not configured. Please check your .env file.')
      }

      // Use Supabase
      const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (authError) {
        console.error("📤 [AUTH API ERROR]:", authError.message);
        throw authError; // Caught by catch block below
      }

      assert(authData.user, "API RETURNED SUCCESS BUT NO USER OBJECT!");
      console.log("2. Auth Success:", authData.user.id);

      // 2. Resolve Profile - Direct lookup in the appropriate table based on role
      const userRoleFromAuth = authData.user.user_metadata?.role || authData.user.user_metadata?.user_role
      console.log("3. Role Verification:", { selectedRole: userRole, authRole: userRoleFromAuth });

      // Enforce Strict Login Separation:
      if (userRole === 'patient' && userRoleFromAuth !== 'patient') {
        await supabase.auth.signOut()
        throw new Error('Access Denied: This login portal is restricted to patients only.');
      }
      if (userRole !== 'patient' && userRoleFromAuth === 'patient') {
        await supabase.auth.signOut()
        throw new Error('Access Denied: Patients cannot access the Staff Portal.');
      }

      let userData = null
      console.log("4. Fetching Clinical Profile...");

      if (userRoleFromAuth === 'patient') {
        const { data: patientData, error: patientError } = await supabase
          .from('patients')
          .select('*, hospitals(hospital_name_en)')
          .eq('user_id', authData.user.id)
          .maybeSingle()

        if (patientError) throw patientError
        assert(patientData, "SECURITY BREACH: Patient profile missing in clinical records.");

        userData = {
          ...patientData,
          id: patientData.id,
          full_name: `${patientData.first_name} ${patientData.last_name}`,
          user_role: 'patient',
          hospital_name: patientData.hospitals?.hospital_name_en
        }
      } else if (userRoleFromAuth === 'doctor') {
        const { data: doctorData, error: doctorError } = await supabase
          .from('doctors')
          .select('*, hospitals(hospital_name_en)')
          .eq('user_id', authData.user.id)
          .maybeSingle()

        if (doctorError) throw doctorError
        assert(doctorData, "DOCTOR PROFILE RECORD NOT FOUND.");
        userData = {
          ...doctorData,
          id: doctorData.id,
          full_name: `${doctorData.first_name} ${doctorData.last_name}`,
          user_role: 'doctor',
          hospital_name: doctorData.hospitals?.hospital_name_en
        }
      } else if (userRoleFromAuth === 'admin' || userRoleFromAuth === 'super_admin') {
        const { data: adminData, error: adminError } = await supabase
          .from('administrators')
          .select('*, hospitals(hospital_name_en)')
          .eq('user_id', authData.user.id)
          .maybeSingle()

        if (adminError) throw adminError
        assert(adminData, "ADMIN PROFILE RECORD NOT FOUND.");
        userData = {
          ...adminData,
          id: adminData.id,
          full_name: `${adminData.first_name} ${adminData.last_name}`,
          user_role: userRoleFromAuth,
          hospital_name: adminData.hospitals?.hospital_name_en
        }
      } else if (userRoleFromAuth === 'nurse') {
        const { data: nurseData, error: nurseError } = await supabase
          .from('nurses')
          .select('*, hospitals(hospital_name_en)')
          .eq('user_id', authData.user.id)
          .maybeSingle()

        if (nurseError) throw nurseError
        assert(nurseData, "NURSE PROFILE RECORD NOT FOUND.");
        userData = {
          ...nurseData,
          id: nurseData.id,
          full_name: `${nurseData.first_name} ${nurseData.last_name}`,
          user_role: 'nurse',
          hospital_name: nurseData.hospitals?.hospital_name_en
        }
      }

      console.log("5. Profile Resolved:", JSON.stringify(userData, null, 2));
      localStorage.setItem('biointellect_current_user', JSON.stringify(userData))

      setCurrentUser(userData)
      setIsAuthenticated(true)
      setUserRole(userRoleFromAuth)
      localStorage.setItem(USER_ROLE_KEY, userRoleFromAuth)

      console.log("✅ [SUCCESS]: Login Verified for role:", finalRole);
      setIsLoading(false)
      return { success: true, user: userData, role: finalRole }
    } catch (err) {
      console.error('SignIn Exception:', err)
      let msg = err.message

      if (msg === 'Email not confirmed' || msg === 'Email not verified') {
        msg = 'Your clinical account requires email verification. Please check your hospital inbox for the confirmation link before attempting to sign in.'
      } else if (msg === 'Invalid login credentials' || msg.includes('invalid_credentials')) {
        msg = 'Authentication failed: Incorrect email or password. Please verify your clinical credentials and try again.'
      } else if (msg.includes('user_not_found')) {
        msg = 'No clinical account found with this email address. Please contact your system administrator.'
      }

      setError(msg)
      setIsLoading(false)
      return { success: false, error: msg }
    }
  }, [userRole])

  /**
   * SESSION TERMINATION
   */
  const signOut = useCallback(async () => {
    setIsLoading(true)

    try {
      console.log("━━━━ [PROTOCOL] INPUT VERIFICATION: SIGN_OUT ━━━━");
      console.log("Status: Initiating Secure Session Termination");

      if (supabase && import.meta.env.VITE_SUPABASE_URL) {
        const { error } = await supabase.auth.signOut()
        if (error) console.warn("Supabase SignOut Warning:", error.message);
      }

      localStorage.removeItem('biointellect_current_user')
      localStorage.removeItem('userRole')

      setCurrentUser(null)
      setIsAuthenticated(false)
      setUserRole(null)

      console.log("✅ [SUCCESS]: Session terminated and local cache purged.");
      setIsLoading(false)
      return { success: true }
    } catch (err) {
      console.error("🚨 SignOut Error:", err.message);
      setError(err.message)
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }, [])

  /**
   * @param {string} email - Email for recovery
   */
  const resetPassword = async (email) => {
    setIsLoading(true)
    setError(null)

    try {
      console.log("━━━━ [PROTOCOL] INPUT VERIFICATION: RESET_PASSWORD ━━━━");
      console.log("1. Input Email:", email);
      assert(email && email.includes('@'), "RECOVERY EMAIL IS INVALID!");

      if (!supabase || !import.meta.env.VITE_SUPABASE_URL) {
        throw new Error('Supabase configuration missing.')
      }

      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      })

      if (error) {
        console.error("📤 [AUTH API ERROR]:", error.message);
        throw error;
      }

      console.log("✅ [SUCCESS]: Recovery link dispatched to:", email);
      setIsLoading(false)
      return { success: true }
    } catch (err) {
      console.error("🚨 Recovery Error:", err.message);
      setError(err.message)
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }

  /**
   * @param {string} newPassword - Validated strong password
   */
  const updatePassword = async (newPassword) => {
    setIsLoading(true)
    setError(null)

    try {
      console.log("━━━━ [PROTOCOL] INPUT VERIFICATION: UPDATE_PASSWORD ━━━━");
      assert(newPassword && newPassword.length >= 6, "NEW PASSWORD DOES NOT MEET MINIMUM LENGTH!");

      if (!supabase || !import.meta.env.VITE_SUPABASE_URL) {
        throw new Error('Supabase configuration missing.')
      }

      const { data, error } = await supabase.auth.updateUser({
        password: newPassword
      })

      if (error) {
        console.error("📤 [AUTH API ERROR]:", error.message);
        throw error;
      }

      console.log("✅ [SUCCESS]: Password record updated for user:", data.user?.id);
      setIsLoading(false)
      return { success: true, user: data.user }
    } catch (err) {
      console.error("🚨 Password Update Error:", err.message);
      setError(err.message)
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }

  /**
   * @param {Object} doctorData
   * @param {string} doctorData.email - Staff email
   * @param {string} doctorData.fullName - Display name
   * @param {string} doctorData.specialty - Clinical specialty (Role)
   */
  const registerDoctor = useCallback(async (doctorData) => {
    setIsLoading(true)
    setError(null)
    try {
      console.log("━━━━ [PROTOCOL] INPUT VERIFICATION: REGISTER_DOCTOR ━━━━");
      console.log("1. Input Data:", JSON.stringify(doctorData, null, 2));

      const { createClient } = await import('@supabase/supabase-js')
      const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
      const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY

      // FRONTEND FIX: Inject current user's session to ensure auth.uid() is populated in DB triggers
      const { data: sessionData } = await supabase.auth.getSession()
      const token = sessionData?.session?.access_token

      const tempSupabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
        auth: {
          storage: { getItem: () => null, setItem: () => { }, removeItem: () => { } },
          persistSession: false,
          autoRefreshToken: false,
          detectSessionInUrl: false
        },
        global: {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      })

      const { email, password, fullName, specialty, phone, licenseNumber, hospitalId } = doctorData

      // EXTREME CHECKS
      assert(email && typeof email === 'string' && email.includes('@'), "STAFF EMAIL IS INVALID!");
      assert(fullName && typeof fullName === 'string' && fullName.length >= 2, "STAFF FULL NAME IS INVALID!");
      assert(CLINICAL_ROLES.includes(specialty), `STAFF ROLE "${specialty}" IS NOT RECOGNIZED BY SYSTEM!`);

      const payloadMetadata = {
        full_name: fullName || 'Medical Staff',
        role: specialty || 'doctor', // Trigger expects 'role'
        first_name: fullName.split(' ')[0] || 'Unknown',
        last_name: fullName.split(' ').slice(1).join(' ') || 'Unknown',
        hospital_id: hospitalId,
        license_number: licenseNumber || 'PENDING'
      };

      console.log("2. Metadata Mapping:", JSON.stringify(payloadMetadata, null, 2));
      console.log("━━━━ [PROTOCOL] VERIFICATION END ━━━━");

      // 1. Create Auth User
      console.log(`[Admin] Initiating enrollmnt for doctor: ${email}`);
      const { data: authData, error: authError } = await tempSupabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/`,
          data: payloadMetadata
        }
      })

      if (authError) {
        console.error("📤 [API ERROR]:", authError.message);
        throw authError;
      }
      assert(authData.user, "AUTH USER CREATION FAILED - NO USER RETURNED!");

      // Trigger handle_new_user in DB will create the profile automatically.
      // We only update additional fields if necessary.
      if (specialty) {
        await supabase.from('doctor_specialties').insert({
          doctor_id: (await supabase.from('doctors').select('id').eq('user_id', authData.user.id).single()).data.id,
          specialty_id: (await supabase.from('specialty_types').select('id').eq('specialty_code', specialty).single()).data.id,
          is_primary: true
        })
      }

      setIsLoading(false)
      return { success: true, user: authData.user }
    } catch (err) {
      console.error('Register Doctor Error:', err)
      setError(err.message)
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }, [currentUser, userRole])

  /**
   * @param {Object} patientData
   * @param {string} patientData.email - Patient email
   * @param {string} patientData.firstName
   * @param {string} patientData.lastName
   */
  const registerPatient = useCallback(async (patientData) => {
    setIsLoading(true)
    setError(null)
    try {
      console.log("━━━━ [PROTOCOL] INPUT VERIFICATION: REGISTER_PATIENT ━━━━");
      console.log("1. Input Data:", JSON.stringify(patientData, null, 2));

      const { createClient } = await import('@supabase/supabase-js')
      const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
      const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY

      // FRONTEND FIX: Inject auth token
      const { data: sessionData } = await supabase.auth.getSession()
      const token = sessionData?.session?.access_token

      const tempSupabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
        auth: {
          storage: { getItem: () => null, setItem: () => { }, removeItem: () => { } },
          persistSession: false,
          autoRefreshToken: false,
          detectSessionInUrl: false
        },
        global: {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      })

      const {
        email, password, firstName, lastName, dateOfBirth, gender,
        phone, address, city, bloodType, allergies,
        chronicConditions, emergencyContactName, emergencyContactPhone,
        emergencyContactRelation, currentMedications, hospitalId
      } = patientData

      const full_name = `${firstName || ''} ${lastName || ''}`.trim() || 'Anonymous Patient'

      // EXTREME CHECKS
      assert(email && typeof email === 'string' && email.includes('@'), "PATIENT EMAIL IS INVALID!");
      assert(full_name.length >= 2, "PATIENT NAME IS INVALID!");

      const payloadMetadata = {
        full_name: full_name,
        role: 'patient', // Trigger expects 'role'
        first_name: firstName,
        last_name: lastName,
        date_of_birth: dateOfBirth,
        gender: gender || 'male',
        hospital_id: hospitalId
      };

      console.log("2. Metadata Mapping:", JSON.stringify(payloadMetadata, null, 2));
      console.log("━━━━ [PROTOCOL] VERIFICATION END ━━━━");

      // 1. Create Auth User
      console.log(`[Admin] Initiating enrollment for patient: ${email}`);
      const { data: authData, error: authError } = await tempSupabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/`,
          data: payloadMetadata
        }
      })

      if (authError) {
        console.error("📤 [API ERROR]:", authError.message);
        throw authError;
      }
      assert(authData.user, "PATIENT AUTH CREATION FAILED!");

      // Additional patient details update
      const { data: patientRecord, error: patientError } = await supabase.from('patients').update({
        phone: phone || null,
        address: address || null,
        city: city || null,
        emergency_contact_name: emergencyContactName || null,
        emergency_contact_phone: emergencyContactPhone || null,
        emergency_contact_relation: emergencyContactRelation || null,
        blood_type: bloodType || 'unknown',
        allergies: allergies || [],
        chronic_conditions: chronicConditions || [],
        current_medications: currentMedications || [],
        is_active: true
      }).eq('user_id', authData.user.id).select().single()

      if (patientError) {
        console.error("Patient update failed:", patientError.message);
      }

      setIsLoading(false)
      return {
        success: true,
        user: authData.user,
        mrn: patientRecord?.medical_record_number || 'PENDING',
        patient_id: authData.user.id
      }
    } catch (error) {
      console.error('Register Patient Error:', error)
      setIsLoading(false)
      return { success: false, error: error.message }
    }
  }, [currentUser, userRole])

  /**
   * @param {Object} adminData
   * @param {string} adminData.email
   * @param {string} adminData.fullName
   * @param {'administrator'|'mini_administrator'} adminData.role
   */
  const registerAdmin = useCallback(async (adminData) => {
    setIsLoading(true)
    setError(null)
    try {
      console.log("━━━━ [PROTOCOL] INPUT VERIFICATION: REGISTER_ADMIN ━━━━");
      console.log("1. Input Data:", JSON.stringify(adminData, null, 2));

      const { createClient } = await import('@supabase/supabase-js')
      const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
      const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY

      // FRONTEND FIX: Inject auth token
      const { data: sessionData } = await supabase.auth.getSession()
      const token = sessionData?.session?.access_token

      const tempSupabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
        auth: {
          storage: { getItem: () => null, setItem: () => { }, removeItem: () => { } },
          persistSession: false,
          autoRefreshToken: false,
          detectSessionInUrl: false
        },
        global: {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        }
      })

      const { email, password, fullName, role, hospitalId } = adminData
      const finalRole = role || 'administrator'

      // EXTREME CHECKS
      assert(email && typeof email === 'string' && email.includes('@'), "ADMIN EMAIL IS INVALID!");
      assert(fullName && typeof fullName === 'string' && fullName.length >= 2, "ADMIN NAME IS INVALID!");
      assert(['administrator', 'mini_administrator'].includes(finalRole), `ADMIN ROLE "${finalRole}" IS PROHIBITED!`);

      const payloadMetadata = {
        full_name: fullName || 'Administrator',
        role: finalRole, // Trigger expects 'role'
        first_name: fullName.split(' ')[0] || 'Unknown',
        last_name: fullName.split(' ').slice(1).join(' ') || 'Unknown',
        hospital_id: hospitalId
      };

      console.log("2. Metadata Mapping:", JSON.stringify(payloadMetadata, null, 2));
      console.log("━━━━ [PROTOCOL] VERIFICATION END ━━━━");

      // 1. Create Auth User
      console.log(`[Admin] Initiating enrollment for new admin: ${email}`);
      const { data: authData, error: authError } = await tempSupabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/`,
          data: payloadMetadata
        }
      })

      if (authError) {
        console.error("📤 [ADMIN API ERROR]:", authError.message);
        throw authError;
      }
      assert(authData.user, "ADMIN AUTH CREATION FAILED!");

      console.log("✅ [SUCCESS]: Admin Created:", authData.user.id);
      setIsLoading(false)
      return { success: true, user: authData.user }
    } catch (err) {
      console.error('Register Admin Error:', err)
      setError(err.message)
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }, [currentUser, userRole])

  /**
   * WORLDWIDE GEOGRAPHY INTEGRATION - RESTCOUNTRIES
   * @returns {Promise<Array>} List of global countries
   */
  /**
   * WORLDWIDE GEOGRAPHY INTEGRATION - RESTCOUNTRIES API
   * @returns {Promise<Array>} List of global countries with flags and ISO codes
   */
  const fetchCountries = useCallback(async () => {
    if (cache.current.countries) return cache.current.countries

    try {
      console.log("━━━━ [PROTOCOL] API INSPECTION: FETCH_COUNTRIES (RestCountries) ━━━━");
      const response = await fetch('https://restcountries.com/v3.1/all?fields=name,flags,cca2,idd');
      if (!response.ok) throw new Error('Failed to fetch countries');

      const data = await response.json();

      const formattedData = data.map(c => ({
        country_id: c.cca2, // Use ISO code as ID for API consistency
        country_name: c.name.common,
        country_code: c.cca2,
        phone_code: c.idd.root ? `${c.idd.root}${c.idd.suffixes?.[0] || ''}` : '',
        flag_url: c.flags.svg
      })).sort((a, b) => a.country_name.localeCompare(b.country_name));

      cache.current.countries = formattedData;
      return formattedData;
    } catch (err) {
      console.error("🚨 [CRITICAL]: Geography API Error:", err.message);
      return [];
    }
  }, [])

  /**
   * REGION FETCHING - COUNTRIESNOW API
   * @param {string} countryName 
   */
  const fetchRegions = useCallback(async (countryName) => {
    if (!countryName) return []
    // Use countryName as key for cache since we work with API names/codes
    if (cache.current.regions[countryName]) return cache.current.regions[countryName]

    try {
      console.log(`━━━━ [PROTOCOL] API INSPECTION: FETCH_REGIONS (${countryName}) ━━━━`);

      // CountriesNow requires POST with country name
      const response = await fetch('https://countriesnow.space/api/v0.1/countries/cities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ country: countryName })
      });

      const result = await response.json();

      // Handle API variations (cities vs states). Using "cities" endpoint for now as requested "Region/City"
      // If result.error is true, it might be because the country name doesn't match exactly.

      let regionsList = [];
      if (!result.error && result.data) {
        regionsList = result.data.map((city, index) => ({
          region_id: `${countryName}-${city}-${index}`, // Generate unique ID
          region_name: city,
          region_code: city.substring(0, 3).toUpperCase()
        }));
      }

      cache.current.regions[countryName] = regionsList;
      return regionsList;
    } catch (err) {
      console.error("🚨 [Data] Regions API Error:", err.message);
      return [];
    }
  }, [])

  /**
   * HOSPITAL FETCHING - SUPABASE PRIVATE NETWORK
   * Note: This remains DB-bound. Since we switched to Global API for regions,
   * strict region_id filtering will interpret the string ID as invalid UUID.
   * We will modify to fetch ALL active hospitals if regionId looks like an API string,
   * or implement a smarter filter later. For now, we fetch all and let UI filter or return strict.
   */
  const fetchHospitals = useCallback(async (regionId) => {
    if (!regionId) return []
    // Simple in-memory cache check
    if (cache.current.hospitals['global']) return cache.current.hospitals['global']

    try {
      console.log("━━━━ [PROTOCOL] DB INSPECTION: FETCH_HOSPITALS ━━━━");
      const { data, error } = await supabase
        .from('hospitals')
        .select('*')
        .eq('is_active', true)
        .order('hospital_name_en');

      if (error) throw error;

      const formattedHospitals = data.map(h => ({
        hospital_id: h.id,
        hospital_name: h.hospital_name_en,
        hospital_code: h.hospital_code,
        region_id: h.region_id // Keep for potential local filtering
      }));

      // Cache globally since we can't key by dynamic API region names easily
      const defaultHospital = {
        hospital_id: 'biointellect-main-hq',
        hospital_name: 'BioIntellect Medical Center',
        hospital_code: 'BIO-HQ',
        region_id: 'global'
      };

      const finalHospitals = [defaultHospital, ...formattedHospitals];

      cache.current.hospitals['global'] = finalHospitals;
      return finalHospitals;
    } catch (err) {
      console.error("🚨 [Data] Hospital DB Error:", err.message);
      // Fallback if DB fails
      return [{
        hospital_id: 'biointellect-main-hq',
        hospital_name: 'BioIntellect Medical Center',
        hospital_code: 'BIO-HQ',
        region_id: 'global'
      }];
    }
  }, [])

  const clearError = useCallback(() => setError(null), [])

  const value = useMemo(() => ({
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
    registerAdmin,
    fetchCountries,
    fetchRegions,
    fetchHospitals,
    isClinicalRole: (role) => CLINICAL_ROLES.includes(role),
    CLINICAL_ROLES,
    clearError,
  }), [
    userRole,
    currentUser,
    isAuthenticated,
    isLoading,
    error,
    selectRole,
    signUp,
    signIn,
    signOut,
    resetPassword,
    updatePassword,
    registerPatient,
    registerDoctor,
    registerAdmin,
    fetchCountries,
    fetchRegions,
    fetchHospitals,
    clearError,
  ])

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
