import { createContext, useContext, useEffect, useState, useCallback, useRef, useMemo } from 'react'
import { authAPI, geographyAPI, setAuthToken, getAuthToken } from '../services/api'
import { ROLES, CLINICAL_ROLES, ROLE_ALIAS_MAP, normalizeRole } from '../config/roles'

const AuthContext = createContext()

const CURRENT_USER_KEY = 'biointellect_current_user'
const USER_ROLE_KEY = 'userRole'

export const AuthProvider = ({ children }) => {
  const [userRole, setUserRole] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [mustResetPassword, setMustResetPassword] = useState(false)
  const [error, setError] = useState(null)

  // ━━━━ CACHING LAYER ━━━━
  const cache = useRef({
    countries: null,
    regions: {},
    hospitals: null
  })

  // ━━━━ INITIALIZATION ━━━━
  useEffect(() => {
    const initSession = async () => {
      try {
        const token = getAuthToken()
        if (!token) {
          setIsLoading(false)
          return
        }

        // Verify session with backend
        const result = await authAPI.getCurrentUser()
        
        if (result.success && result.user) {
          const userData = {
            ...result.user.profile,
            user_id: result.user.id,
            email: result.user.email,
            user_role: result.user.role
          }
          
          setCurrentUser(userData)
          setIsAuthenticated(true)
          setUserRole(result.user.role)
          localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(userData))
          localStorage.setItem(USER_ROLE_KEY, result.user.role)
        } else {
          // Token invalid, clear everything
          setAuthToken(null)
          localStorage.removeItem(CURRENT_USER_KEY)
          localStorage.removeItem(USER_ROLE_KEY)
        }
      } catch (err) {
        console.error('🚨 [SESSION]: Init Error:', err)
        // Clear invalid session
        setAuthToken(null)
        localStorage.removeItem(CURRENT_USER_KEY)
        localStorage.removeItem(USER_ROLE_KEY)
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

  const signIn = useCallback(async (email, password) => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await authAPI.signIn(email, password)
      
      if (!result.success) {
        throw new Error(result.message || 'Login failed')
      }

      const authRole = result.user.role
      
      // Check role restriction
      if (userRole === ROLES.PATIENT && authRole !== ROLES.PATIENT) {
        await authAPI.signOut()
        throw new Error("Restricted: Patient Portal Only")
      }

      const userData = {
        ...result.user.profile,
        user_id: result.user.id,
        email: result.user.email,
        user_role: authRole
      }

      setCurrentUser(userData)
      setIsAuthenticated(true)
      setUserRole(authRole)
      setMustResetPassword(result.must_reset_password || false)
      localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(userData))
      localStorage.setItem(USER_ROLE_KEY, authRole)
      
      setIsLoading(false)
      return { success: true, user: userData, role: authRole, mustReset: result.must_reset_password }

    } catch (err) {
      setError(err.message)
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }, [userRole])

  const signUp = useCallback(async (signUpData) => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await authAPI.signUp({
        email: signUpData.email,
        password: signUpData.password,
        role: signUpData.role,
        first_name: signUpData.firstName || signUpData.first_name,
        last_name: signUpData.lastName || signUpData.last_name,
        phone: signUpData.phone,
        hospital_id: signUpData.hospitalId || signUpData.hospital_id,
        license_number: signUpData.licenseNumber || signUpData.license_number,
        specialty: signUpData.specialty
      })

      if (!result.success) {
        throw new Error(result.message || 'Registration failed')
      }

      setIsLoading(false)
      return { success: true, userId: result.user_id }
    } catch (err) {
      setError(err.message)
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }, [])

  const registerPatient = useCallback(async (data) => {
    return signUp({ ...data, role: ROLES.PATIENT })
  }, [signUp])

  const registerDoctor = useCallback(async (data) => {
    return signUp({ ...data, role: ROLES.DOCTOR })
  }, [signUp])

  const registerAdmin = useCallback(async (data) => {
    const role = data.role === 'super_admin' ? ROLES.SUPER_ADMIN : ROLES.ADMIN
    return signUp({ ...data, role })
  }, [signUp])

  const completeForcedReset = useCallback(async (newPassword) => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await authAPI.updatePassword(newPassword)
      
      if (!result.success) {
        throw new Error(result.message || 'Password update failed')
      }

      setMustResetPassword(false)
      setIsLoading(false)
      return { success: true }
    } catch (err) {
      setError(err.message)
      setIsLoading(false)
      return { success: false, error: err.message }
    }
  }, [])

  const signOut = useCallback(async () => {
    await authAPI.signOut()
    setCurrentUser(null)
    setIsAuthenticated(false)
    setUserRole(null)
    setMustResetPassword(false)
  }, [])

  const refreshUser = useCallback(async () => {
    try {
      const result = await authAPI.getCurrentUser()
      
      if (result.success && result.user) {
        const userData = {
          ...result.user.profile,
          user_id: result.user.id,
          email: result.user.email,
          user_role: result.user.role
        }
        setCurrentUser(userData)
        localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(userData))
        return userData
      }
    } catch (err) {
      console.error('🚨 [AUTH]: Refresh Error:', err)
    }
    return null
  }, [])

  // ─── GEOGRAPHY & HELPERS ───
  const fetchCountries = useCallback(async () => {
    if (cache.current.countries) return cache.current.countries
    try {
      // Use external API for countries (more data)
      const res = await fetch('https://restcountries.com/v3.1/all?fields=name,flags,cca2,idd')
      const data = await res.json()
      const formatted = data.map(c => ({
        country_id: c.cca2, 
        country_name: c.name.common, 
        country_code: c.cca2,
        phone_code: c.idd.root ? `${c.idd.root}${c.idd.suffixes?.[0] || ''}` : '', 
        flag_url: c.flags.svg
      })).sort((a, b) => a.country_name.localeCompare(b.country_name))
      cache.current.countries = formatted
      return formatted
    } catch (e) { 
      // Fallback to backend
      try {
        const result = await geographyAPI.listCountries()
        if (result.success) {
          const formatted = result.data.map(c => ({
            country_id: c.id,
            country_name: c.country_name_en,
            country_code: c.country_code,
            phone_code: c.phone_code
          }))
          cache.current.countries = formatted
          return formatted
        }
      } catch (e2) {}
      return [] 
    }
  }, [])

  const fetchRegions = useCallback(async (countryName) => {
    if (!countryName) return []
    if (cache.current.regions[countryName]) return cache.current.regions[countryName]
    try {
      const res = await fetch('https://countriesnow.space/api/v0.1/countries/cities', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ country: countryName })
      })
      const result = await res.json()
      if (result.data) {
        const regions = result.data.map((city, idx) => ({ region_id: `${countryName}-${city}-${idx}`, region_name: city }))
        cache.current.regions[countryName] = regions
        return regions
      }
      return []
    } catch (e) { return [] }
  }, [])

  const fetchHospitals = useCallback(async () => {
    if (cache.current.hospitals) return cache.current.hospitals
    try {
      const result = await geographyAPI.listHospitals()
      
      if (result.success && result.data) {
        const formatted = result.data.map(h => ({
          hospital_id: h.id,
          hospital_name: h.hospital_name_en
        }))
        cache.current.hospitals = formatted
        return formatted
      }
      return [{ hospital_id: 'biointellect-main-hq', hospital_name: 'BioIntellect Medical Center (Fallback)' }]
    } catch (e) {
      console.error("🚨 [FETCH HOSPITALS ERROR]:", e.message)
      return [{ hospital_id: 'biointellect-main-hq', hospital_name: 'BioIntellect Medical Center (Fallback)' }]
    }
  }, [])

  const clearError = useCallback(() => setError(null), [])

  const value = useMemo(() => ({
    userRole, currentUser, isAuthenticated, isLoading, error, mustResetPassword,
    selectRole, signUp, signIn, signOut, refreshUser, completeForcedReset,
    registerPatient, registerDoctor, registerAdmin,
    fetchCountries, fetchRegions, fetchHospitals,
    clearError,
    CLINICAL_ROLES
  }), [userRole, currentUser, isAuthenticated, isLoading, error, mustResetPassword, selectRole, signUp, signIn, signOut, refreshUser, completeForcedReset, registerPatient, registerDoctor, registerAdmin, fetchCountries, fetchRegions, fetchHospitals, clearError])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}

export default AuthContext
