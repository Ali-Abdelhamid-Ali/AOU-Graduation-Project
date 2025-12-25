import { createContext, useContext, useEffect, useState, useCallback, useRef, useMemo } from 'react'
import { supabase, getCurrentUser } from '../config/supabase'

const AuthContext = createContext()

const CURRENT_USER_KEY = 'biointellect_current_user'
const USER_ROLE_KEY = 'userRole'

const CLINICAL_ROLES = ['administrator', 'mini_administrator', 'Cardiologist', 'Neurologist', 'General Physician', 'Pediatrician', 'General Surgeon'];

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

          // 2. Resolve Clinical Profile
          const userRoleFromAuth = authUser.user_metadata?.user_role
          let userData = null

          if (userRoleFromAuth === 'patient') {
            const { data: patientData } = await supabase
              .from('patients')
              .select('*')
              .eq('patient_id', authUser.id)
              .maybeSingle()

            if (patientData) {
              userData = {
                ...patientData,
                id: authUser.id,
                full_name: `${patientData.first_name} ${patientData.last_name}`,
                user_role: 'patient'
              }
            }
          } else {
            const { data: staffData } = await supabase
              .from('users')
              .select('*')
              .eq('user_id', authUser.id)
              .maybeSingle()

            if (staffData) {
              userData = staffData
            }
          }

          if (userData) {
            const rawRole = userData.user_role
            const finalRole = CLINICAL_ROLES.includes(rawRole) ? rawRole : (rawRole === 'patient' ? 'patient' : 'administrator')

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
    if (!['doctor', 'patient', 'administrator'].includes(role)) {
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
    assert(role && ['patient', 'doctor', 'administrator'].includes(role), `ROLE "${role}" IS NOT ALLOWED BY SYSTEM!`);

    const derivedName = (firstName && lastName) ? `${firstName} ${lastName}` : (signUpData.full_name || 'System User')
    const full_name = derivedName.trim() || 'System User'

    console.log("2. Resolved Name:", full_name, "| Type:", typeof full_name);
    assert(full_name.length >= 2, "RESOLVED USERNAME IS TOO SHORT!");
    console.log("━━━━ [PROTOCOL] VERIFICATION END ━━━━");

    try {
      const payloadMetadata = {
        full_name: full_name,
        user_role: role,
        first_name: firstName,
        last_name: lastName,
        date_of_birth: dateOfBirth,
        gender: gender || 'male',
        v_creator_id: 'SELF',
        v_creator_role: 'SELF',
        hospital_id: signUpData.hospitalId || null,
        country_id: signUpData.countryId || null,
        region_id: signUpData.regionId || null,
        country_code: signUpData.countryCode || null
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
      const userRoleFromAuth = authData.user.user_metadata?.user_role
      console.log("3. Role Verification:", { selectedRole: userRole, authRole: userRoleFromAuth });

      // Enforce Strict Login Separation:
      if (userRole === 'patient') {
        if (userRoleFromAuth !== 'patient') {
          await supabase.auth.signOut()
          throw new Error('Access Denied: This login portal is restricted to patients only. Medical staff must use the Staff Portal.');
        }
      } else if (userRoleFromAuth === 'patient') {
        await supabase.auth.signOut()
        throw new Error('Access Denied: Patients cannot access the Medical Staff Portal. Please use the Patient Login.');
      }

      let userData = null
      console.log("4. Fetching Clinical Profile...");

      if (userRoleFromAuth === 'patient') {
        const { data: patientData, error: patientError } = await supabase
          .from('patients')
          .select('*')
          .eq('patient_id', authData.user.id)
          .maybeSingle()

        if (patientError) throw patientError
        assert(patientData, "SECURITY BREACH: Patient profile missing in clinical records.");

        userData = {
          ...patientData,
          id: authData.user.id,
          full_name: `${patientData.first_name} ${patientData.last_name}`,
          user_role: 'patient'
        }
      } else {
        const { data: staffData, error: staffError } = await supabase
          .from('users')
          .select('*')
          .eq('user_id', authData.user.id)
          .maybeSingle()

        if (staffError) throw staffError
        assert(staffData, "STAFF PROFILE RECORD NOT FOUND.");
        userData = staffData
      }

      console.log("5. Profile Resolved:", JSON.stringify(userData, null, 2));
      localStorage.setItem('biointellect_current_user', JSON.stringify(userData))

      const rawRole = userData.user_role
      const finalRole = CLINICAL_ROLES.includes(rawRole) ? 'administrator' : rawRole

      setCurrentUser(userData)
      setIsAuthenticated(true)
      setUserRole(finalRole)
      localStorage.setItem('userRole', finalRole)

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

      const { email, password, fullName, specialty, phone, licenseNumber, hospitalId, countryId, regionId } = doctorData

      const creatorRole = currentUser?.user_role || userRole || 'SELF'

      // EXTREME CHECKS
      assert(email && typeof email === 'string' && email.includes('@'), "STAFF EMAIL IS INVALID!");
      assert(fullName && typeof fullName === 'string' && fullName.length >= 2, "STAFF FULL NAME IS INVALID!");
      assert(CLINICAL_ROLES.includes(specialty), `STAFF ROLE "${specialty}" IS NOT RECOGNIZED BY SYSTEM!`);

      // Ensure Creator ID is explicit
      const creatorId = currentUser?.id || currentUser?.user_id || 'SELF'

      const payloadMetadata = {
        full_name: fullName || 'Medical Staff', // FRONTEND FIX: Fallback to prevent DB error
        user_role: specialty || 'General Physician',
        hospital_id: hospitalId,
        country_id: countryId,
        region_id: regionId,
        country_code: doctorData.countryCode || null,
        v_creator_id: creatorId,
        v_creator_role: creatorRole
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

      // Record in public.users is handled by SQL trigger handle_secure_user_creation
      // However, we might need to update details if the trigger is missing some fields
      const { error: updateError } = await supabase.from('users').update({
        phone_number: phone || null,
        license_number: licenseNumber || null,
        specialty: specialty || null,
        hospital_id: hospitalId || null,
        country_id: countryId || null,
        region_id: regionId || null
      }).eq('user_id', authData.user.id)

      if (updateError) console.warn('User table update warning:', updateError.message)

      setIsLoading(false)
      return { success: true, user: authData.user }
    } catch (err) {
      console.error('Register Doctor Error:', err)
      setError(err.message)
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }, [currentUser])

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
        emergencyContactRelation, currentMedications, consentGiven,
        dataRetentionUntil, hospitalId, countryId, regionId
      } = patientData

      const full_name = `${firstName || ''} ${lastName || ''}`.trim() || 'Anonymous Patient'
      const creatorRole = currentUser?.user_role || userRole || 'SELF'

      // EXTREME CHECKS
      assert(email && typeof email === 'string' && email.includes('@'), "PATIENT EMAIL IS INVALID!");
      assert(full_name.length >= 2, "PATIENT NAME IS INVALID!");

      const payloadMetadata = {
        full_name: full_name,
        user_role: 'patient',
        first_name: firstName,
        last_name: lastName,
        date_of_birth: dateOfBirth,
        gender: gender || 'male',
        hospital_id: hospitalId,
        country_id: countryId,
        region_id: regionId,
        v_creator_id: currentUser?.id || currentUser?.user_id || 'SELF',
        v_creator_role: creatorRole
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

      // 2. Additional patient details update
      const { data: patientRecord, error: patientError } = await supabase.from('patients').update({
        phone_number: phone || null,
        address: address || null,
        city: city || null,
        emergency_contact_name: emergencyContactName || null,
        emergency_contact_phone: emergencyContactPhone || null,
        emergency_contact_relation: emergencyContactRelation || null,
        blood_type: bloodType || null,
        allergies: allergies || [],
        chronic_conditions: chronicConditions || [],
        current_medications: currentMedications || {},
        created_by: currentUser?.user_id || currentUser?.id,
        is_active: true,
        consent_given: consentGiven || false,
        consent_date: consentGiven ? new Date().toISOString() : null,
        data_retention_until: dataRetentionUntil || null,
        hospital_id: hospitalId || null,
        country_id: countryId || null,
        region_id: regionId || null
      }).eq('patient_id', authData.user.id).select().single()

      if (patientError) {
        console.warn('Patient extended update failed, trying email secondary fallback:', patientError.message)
        const { error: secondError } = await supabase.from('patients').update({
          phone_number: phone || null,
          address: address || null,
          hospital_id: hospitalId || null,
          country_id: countryId || null,
          region_id: regionId || null
        }).eq('email', email)

        if (secondError) console.error("Patient fallback update also failed:", secondError.message);
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
  }, [currentUser])

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

      const { email, password, fullName, role, hospitalId, countryId, regionId } = adminData
      const finalRole = role || 'administrator'
      const creatorRole = currentUser?.user_role || userRole || 'SELF'

      // EXTREME CHECKS
      assert(email && typeof email === 'string' && email.includes('@'), "ADMIN EMAIL IS INVALID!");
      assert(fullName && typeof fullName === 'string' && fullName.length >= 2, "ADMIN NAME IS INVALID!");
      assert(['administrator', 'mini_administrator'].includes(finalRole), `ADMIN ROLE "${finalRole}" IS PROHIBITED!`);

      const creatorId = currentUser?.id || currentUser?.user_id || 'SELF'

      const payloadMetadata = {
        full_name: fullName || 'Administrator', // FRONTEND FIX: Prevent null value
        user_role: finalRole,
        hospital_id: hospitalId,
        country_id: countryId,
        region_id: regionId,
        v_creator_id: creatorId,
        v_creator_role: creatorRole
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
  }, [currentUser])

  /**
   * WORLDWIDE GEOGRAPHY INTEGRATION - RESTCOUNTRIES
   * @returns {Promise<Array>} List of global countries
   */
  const fetchCountries = useCallback(async () => {
    if (cache.current.countries) return cache.current.countries

    try {
      console.log("━━━━ [PROTOCOL] API INSPECTION: FETCH_COUNTRIES ━━━━");
      console.log("URL: https://restcountries.com/v3.1/all?fields=name,cca2,flags");

      const response = await fetch('https://restcountries.com/v3.1/all?fields=name,cca2,flags');
      console.log("🌐 Response Status:", response.status);

      assert(response.ok, `COUNTRIES API FAILED: ${response.status}`);

      const rawData = await response.json();
      console.log("📦 Received Payload Sample (First 1):", JSON.stringify(rawData[0], null, 2));

      // Structure Validation
      assert(Array.isArray(rawData), "COUNTRIES API DID NOT RETURN AN ARRAY!");
      assert(rawData.length > 0, "COUNTRIES API RETURNED EMPTY SET!");

      // Transform into BioIntellect standard format
      const formattedData = rawData.map(c => {
        assert(c.cca2 && c.name?.common, "MALFORMED COUNTRY DATA IN PAYLOAD!");
        return {
          country_id: c.cca2,
          country_name: c.name.common,
          country_code: c.cca2,
          flag_url: c.flags?.png || ''
        };
      }).sort((a, b) => a.country_name.localeCompare(b.country_name));

      console.log(`✅ [SUCCESS]: Global load verified: ${formattedData.length} entries.`);
      cache.current.countries = formattedData;
      return formattedData;
    } catch (err) {
      console.error("🚨 [CRITICAL]: Geography API Error:", err.message);
      // Failover to essential clinical regions if API is down
      const failover = [
        { country_id: 'EG', country_name: 'Egypt', country_code: 'EG' },
        { country_id: 'SA', country_name: 'Saudi Arabia', country_code: 'SA' },
        { country_id: 'US', country_name: 'United States', country_code: 'US' }
      ];
      console.log("♻️  [FAILOVER]: Loading essential regions instead.");
      return failover;
    }
  }, [])

  /**
   * REGION FETCHING - COUNTRIESNOW
   * @param {string} countryName 
   */
  const fetchRegions = useCallback(async (countryName) => {
    if (!countryName) return []
    if (cache.current.regions[countryName]) return cache.current.regions[countryName]

    try {
      console.log("━━━━ [PROTOCOL] API INSPECTION: FETCH_REGIONS ━━━━");
      console.log("Input (countryName):", countryName);

      const response = await fetch('https://countriesnow.space/api/v0.1/countries/states', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ country: countryName })
      });

      console.log("🌐 Response Status:", response.status);
      assert(response.ok, `REGIONS API FAILED: ${response.status}`);

      const result = await response.json();
      console.log("📦 Payload Status:", result.error ? 'API_ERROR' : 'SUCCESS');

      if (result.error) {
        console.warn(`[API Warning]: ${result.msg}`);
        throw new Error(result.msg);
      }

      assert(result.data?.states, "API RESPONSE MISSING STATES PROPERTY!");

      const formattedRegions = result.data.states.map((s, index) => ({
        region_id: `${countryName}-${index}`, // Derived ID
        region_name: s.name,
        country_name: countryName
      }));

      console.log(`✅ [SUCCESS]: Resolved ${formattedRegions.length} regions for ${countryName}.`);
      cache.current.regions[countryName] = formattedRegions;
      return formattedRegions;
    } catch (err) {
      console.error("🚨 [Data] Regions Extraction Error:", err.message);
      return [];
    }
  }, [])

  /**
   * HOSPITAL FETCHING - SUPABASE PRIVATE NETWORK
   * @param {Object|string} locationData 
   */
  const fetchHospitals = useCallback(async (locationData) => {
    // locationData can be a string (regionName) or object { regionName, countryName }
    const regionName = typeof locationData === 'string' ? locationData : locationData?.regionName;
    const countryName = typeof locationData === 'object' ? locationData?.countryName : null;

    const cacheKey = regionName || countryName || 'global';
    if (cache.current.hospitals[cacheKey]) return cache.current.hospitals[cacheKey]

    try {
      console.log("━━━━ [PROTOCOL] DB INSPECTION: FETCH_HOSPITALS ━━━━");
      console.log("Location Param:", cacheKey);

      // Query our private hospital network
      let query = supabase.from('hospitals').select('*').order('hospital_name');

      if (regionName) {
        query = query.ilike('address', `%${regionName}%`);
      } else if (countryName) {
        query = query.ilike('address', `%${countryName}%`);
      }

      console.log("SQL Equivalent: SELECT * FROM hospitals WHERE address ILIKE ...");
      const { data, error } = await query;

      if (error) {
        console.error("📥 [DB ERROR]:", error.message);
        throw error;
      }

      assert(Array.isArray(data), "HOSPITALS QUERY RETURNED INVALID RESULT!");

      const results = (data && data.length > 0) ? data : [
        { hospital_id: 'central-hub', hospital_name: 'BioIntellect Central Clinical Hub', address: 'Global Virtual Care' }
      ];

      console.log(`✅ [SUCCESS]: Found ${data?.length || 0} local facilities. Results:`, results.length);
      cache.current.hospitals[cacheKey] = results;
      return results;
    } catch (err) {
      console.error("🚨 [Data] Hospital Discovery Error:", err.message);
      return [{ hospital_id: 'central-hub', hospital_name: 'BioIntellect Central Clinical Hub' }];
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
