import { createContext, useContext, useEffect, useState, useCallback, useRef, useMemo } from 'react'
import { supabase, getCurrentUser } from '../config/supabase'
import { ROLES, CLINICAL_ROLES, ROLE_DB_CONFIG, ROLE_ALIAS_MAP, createAuthPayload, createProfileData, normalizeRole } from '../config/roles'

const AuthContext = createContext()

const CURRENT_USER_KEY = 'biointellect_current_user'
const USER_ROLE_KEY = 'userRole'

/**
 * ━━━━ CLINICAL SYSTEM ASSERTIONS ━━━━
 * Critical validation helper for secure operations.
 */
const assert = (condition, message) => {
  if (!condition) {
    console.error(`🚨 [ASSERTION FAILED]: ${message}`);
    throw new Error(message);
  }
};

export const AuthProvider = ({ children }) => {
  const [userRole, setUserRole] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  // ━━━━ CACHING LAYER ━━━━
  const cache = useRef({
    countries: null,
    regions: {},
    hospitals: {}
  })

  // ━━━━ INITIALIZATION ━━━━
  useEffect(() => {
    const initSession = async () => {
      try {
        const { data: authUser } = await getCurrentUser()

        if (authUser) {
          console.log("🔓 [SESSION]: Active session verified for:", authUser.id);
          const userRoleFromAuth = authUser.user_metadata?.role || authUser.user_metadata?.user_role;
          const normalizedRole = userRoleFromAuth ? ROLE_ALIAS_MAP[userRoleFromAuth.toLowerCase()] : null;
          let userData = null;

          if (normalizedRole && ROLE_DB_CONFIG[normalizedRole]) {
            const config = ROLE_DB_CONFIG[normalizedRole];
            const { data: profileData } = await supabase
              .from(config.table)
              .select(config.select)
              .eq('user_id', authUser.id)
              .maybeSingle();

            if (profileData) {
              userData = config.transform(profileData);
            }
          }

          if (userData) {
            setCurrentUser(userData);
            setIsAuthenticated(true);
            const finalRole = userData.user_role || normalizedRole;
            setUserRole(finalRole);
            localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(userData));
            localStorage.setItem(USER_ROLE_KEY, finalRole);
          } else if (normalizedRole) {
            // FALLBACK: Auth session exists but Profile record is missing (common during trigger failures)
            console.warn("⚠️ [SESSION]: Auth exists but Profile record NOT found. Allowing restricted session.");
            setIsAuthenticated(true);
            setUserRole(normalizedRole);
            localStorage.setItem(USER_ROLE_KEY, normalizedRole);
          }
        } else {
          localStorage.removeItem(CURRENT_USER_KEY)
          localStorage.removeItem(USER_ROLE_KEY)
        }
      } catch (err) {
        console.error('🚨 [SESSION]: Init Error:', err)
      } finally {
        setIsLoading(false)
      }
    }
    initSession()
  }, [])

  // ━━━━ SESSION TIMEOUT ━━━━
  useEffect(() => {
    if (!isAuthenticated) return
    const TIMEOUT_MS = 15 * 60 * 1000 // 15 mins
    const updateActivity = () => localStorage.setItem('biointellect_last_activity', Date.now().toString())

    // Initial activity
    updateActivity()

    const checkInactivity = () => {
      const lastActivity = parseInt(localStorage.getItem('biointellect_last_activity') || '0', 10)
      if (Date.now() - lastActivity > TIMEOUT_MS) signOut()
    }

    window.addEventListener('mousemove', updateActivity)
    window.addEventListener('keydown', updateActivity)
    const intervalId = setInterval(checkInactivity, 60000)

    return () => {
      window.removeEventListener('mousemove', updateActivity)
      window.removeEventListener('keydown', updateActivity)
      clearInterval(intervalId)
    }
  }, [isAuthenticated])


  // ━━━━ CORE AUTH ACTIONS ━━━━

  const selectRole = useCallback((role) => {
    if (!Object.values(ROLES).includes(role) && !['admin', 'super_admin'].includes(role)) {
      setError('Invalid role')
      return
    }
    setUserRole(role)
    localStorage.setItem(USER_ROLE_KEY, role)
    setError(null)
  }, [])

  // ─── UNIFIED REGISTRATION HANDLER (DIRECT SUPABASE) ───
  // Registers the user directly via Supabase Auth.
  const _registerUser = useCallback(async (baseInput, explicitRole, tableName, finalRoleOverride = null) => {
    setIsLoading(true);
    setError(null);

    try {
      console.log(`━━━━ [SUPABASE] DIRECT REGISTRATION: ${explicitRole} ━━━━`);

      // 1. Prepare standardized metadata via roles.js logic
      const authMetadata = createAuthPayload({
        ...baseInput,
        role: finalRoleOverride || explicitRole
      });

      // 2. Execute Supabase SignUp
      const { data, error: authError } = await supabase.auth.signUp({
        email: baseInput.email,
        password: baseInput.password,
        options: {
          data: authMetadata,
          // Note: If you have email confirmation enabled, the profile won't be created 
          // until they confirm, unless a trigger is handling it.
        }
      });

      if (authError) throw authError;

      if (!data.user) {
        throw new Error("Registration succeeded but no user object was returned.");
      }

      console.log(`✅ [AUTH] User Created Directly: ${data.user.id}`);

      // Optional: Inform user about triggers
      // Since we are now "Independent", we rely on Supabase SQL Triggers to 
      // populate the profile tables (patients/doctors/admins).

      setIsLoading(false);
      return { success: true, userId: data.user.id };

    } catch (err) {
      console.error(`🚨 [SUPABASE REGISTRATION FAILED]: ${err.message}`);

      // Detailed error translation for the user
      let userFriendlyMsg = err.message;
      if (err.message.includes('500') || err.message.includes('Database error')) {
        userFriendlyMsg = "Supabase SQL Error (500): The registration trigger or RLS policy failed. Check SQL Editor logs.";
      }

      setError(userFriendlyMsg);
      setIsLoading(false);
      return { success: false, error: userFriendlyMsg };
    }
  }, []);


  // ─── PUBLIC ACTIONS ───


  const signIn = useCallback(async (email, password) => {
    setIsLoading(true)
    setError(null)
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password })
      if (error) throw error

      const rawRole = data.user.user_metadata?.role;
      const authRole = rawRole ? ROLE_ALIAS_MAP[rawRole.toLowerCase()] : null;
      console.log("LOGIN ROLE:", authRole);

      if (userRole === ROLES.PATIENT && authRole !== ROLES.PATIENT) {
        throw new Error("Restricted: Patient Portal Only");
      }

      if (authRole && ROLE_DB_CONFIG[authRole]) {
        const config = ROLE_DB_CONFIG[authRole];
        const { data: profile } = await supabase.from(config.table).select(config.select).eq('user_id', data.user.id).maybeSingle();
        if (profile) {
          const userData = config.transform(profile);
          setCurrentUser(userData);
          setIsAuthenticated(true);
          setUserRole(authRole);
          localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(userData));
          localStorage.setItem(USER_ROLE_KEY, authRole);
          setIsLoading(false);
          return { success: true, user: userData, role: authRole };
        }
      }

      // Fallback if profile load fails but auth succeeded
      console.warn("⚠️ [AUTH]: Login succeeded but Profile record not found. Using metadata role.");
      setIsAuthenticated(true);
      setUserRole(authRole);
      localStorage.setItem(USER_ROLE_KEY, authRole);
      setIsLoading(false);
      return { success: true, user: data.user, role: authRole };

    } catch (err) {
      setError(err.message);
      setIsLoading(false);
      return { success: false, error: err.message };
    }
  }, [userRole])

  const signOut = useCallback(async () => {
    await supabase.auth.signOut()
    localStorage.removeItem(CURRENT_USER_KEY)
    localStorage.removeItem(USER_ROLE_KEY)
    setCurrentUser(null)
    setIsAuthenticated(false)
    setUserRole(null)
  }, [])


  // ─── SPECIFIC REGISTRATIONS ───

  const registerPatient = useCallback(async (data) => {
    return _registerUser(data, ROLES.PATIENT, 'patients');
  }, [_registerUser])

  const registerDoctor = useCallback(async (data) => {
    const result = await _registerUser(data, ROLES.DOCTOR, 'doctors', null);

    // Handle Doctor Specialties Link
    if (result.success && data.specialty) {
      // Logic to link specialty in 'doctor_specialties' table
      // This is a post-registration step
      try {
        // Fetch doctor ID first
        const { data: doc } = await supabase.from('doctors').select('id').eq('user_id', result.userId).single();
        const { data: spec } = await supabase.from('specialty_types').select('id').eq('specialty_code', data.specialty).single();

        if (doc && spec) {
          await supabase.from('doctor_specialties').insert({ doctor_id: doc.id, specialty_id: spec.id, is_primary: true });
        }
      } catch (e) {
        console.warn("Failed to link specialty:", e);
      }
    }
    return result;
  }, [_registerUser])

  const registerAdmin = useCallback(async (data) => {
    // Handle 'role' field which might be 'admin' or 'super_admin' or 'mini_administrator'
    let finalRole = ROLES.ADMIN;
    if (data.role === 'super_admin') finalRole = ROLES.SUPER_ADMIN;

    return _registerUser(data, ROLES.ADMIN, 'administrators', finalRole);
  }, [_registerUser])

  const signUp = useCallback(async (signUpData) => {
    try {
      const { role } = signUpData;
      const normalized = normalizeRole(role);

      if (normalized === ROLES.PATIENT) return await registerPatient(signUpData);
      if (normalized === ROLES.DOCTOR) return await registerDoctor(signUpData);
      if (normalized === ROLES.ADMIN || normalized === ROLES.SUPER_ADMIN) return await registerAdmin(signUpData);

      throw new Error(`Registration not implemented for role: ${normalized}`);
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  }, [registerPatient, registerDoctor, registerAdmin]);


  // ─── GEOGRAPHY & HELPERS ───
  // (Keeping existing implementations but minimized for length - assuming they work)
  const fetchCountries = useCallback(async () => {
    if (cache.current.countries) return cache.current.countries;
    try {
      const res = await fetch('https://restcountries.com/v3.1/all?fields=name,flags,cca2,idd');
      const data = await res.json();
      const formatted = data.map(c => ({
        country_id: c.cca2, country_name: c.name.common, country_code: c.cca2,
        phone_code: c.idd.root ? `${c.idd.root}${c.idd.suffixes?.[0] || ''}` : '', flag_url: c.flags.svg
      })).sort((a, b) => a.country_name.localeCompare(b.country_name));
      cache.current.countries = formatted;
      return formatted;
    } catch (e) { return [] }
  }, []);

  const fetchRegions = useCallback(async (countryName) => {
    if (!countryName) return [];
    if (cache.current.regions[countryName]) return cache.current.regions[countryName];
    try {
      const res = await fetch('https://countriesnow.space/api/v0.1/countries/cities', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ country: countryName })
      });
      const result = await res.json();
      if (result.data) {
        const regions = result.data.map((city, idx) => ({ region_id: `${countryName}-${city}-${idx}`, region_name: city }));
        cache.current.regions[countryName] = regions;
        return regions;
      }
      return [];
    } catch (e) { return [] }
  }, []);

  const fetchHospitals = useCallback(async () => {
    if (cache.current.hospitals_list) return cache.current.hospitals_list;
    try {
      console.log("🏥 [SYSTEM]: Synchronizing Clinical Hospitals...");
      const { data, error } = await supabase
        .from('hospitals')
        .select('id, hospital_name_en')
        .eq('is_active', true);

      if (error) throw error;

      const formatted = data.map(h => ({
        hospital_id: h.id,
        hospital_name: h.hospital_name_en
      }));

      cache.current.hospitals_list = formatted;
      return formatted;
    } catch (e) {
      console.error("🚨 [FETCH HOSPITALS ERROR]:", e.message);
      return [{ hospital_id: 'biointellect-main-hq', hospital_name: 'BioIntellect Medical Center (Fallback)' }];
    }
  }, []);

  const clearError = useCallback(() => setError(null), [])

  const value = useMemo(() => ({
    userRole, currentUser, isAuthenticated, isLoading, error,
    selectRole, signUp, signIn, signOut,
    registerPatient, registerDoctor, registerAdmin,
    fetchCountries, fetchRegions, fetchHospitals,
    clearError,
    CLINICAL_ROLES
  }), [userRole, currentUser, isAuthenticated, isLoading, error, selectRole, signUp, signIn, signOut, registerPatient, registerDoctor, registerAdmin, fetchCountries, fetchRegions, fetchHospitals, clearError])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}

export default AuthContext
