import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import { authAPI, usersAPI, geographyAPI } from '@/services/api'
import { ROLES, CLINICAL_ROLES, ROLE_ALIAS_MAP, normalizeRole } from '@/config/roles'

const AuthContext = createContext()

const CURRENT_USER_KEY = 'biointellect_current_user'
const ACCESS_TOKEN_KEY = 'biointellect_access_token'
const USER_ROLE_KEY = 'biointellect_user_role'

const normalizeApiError = (err, fallback) => err?.detail || err?.message || fallback

const toBackendRole = (role) => {
  if (!role) return role

  try {
    const normalized = normalizeRole(role)
    return normalized === ROLES.ADMIN ? 'admin' : normalized
  } catch {
    return role
  }
}

const buildPublicSignUpPayload = (data, fallbackRole) => ({
  email: data.email,
  password: data.password,
  role: toBackendRole(data.role || fallbackRole),
  first_name: data.first_name || data.firstName,
  last_name: data.last_name || data.lastName,
  phone: data.phone || '',
  hospital_id: data.hospital_id || data.hospitalId,
  country_id: data.country_id || data.countryId,
  region_id: data.region_id || data.regionId,
  employee_id: data.employee_id || data.employeeId,
  department: data.department,
})

const buildPatientPayload = (data) => ({
  hospital_id: data.hospital_id || data.hospitalId,
  first_name: data.first_name || data.firstName,
  last_name: data.last_name || data.lastName,
  email: data.email,
  password: data.password,
  phone: data.phone || '',
  date_of_birth: data.date_of_birth || data.dateOfBirth,
  gender: data.gender,
  first_name_ar: data.first_name_ar || data.firstNameAr,
  last_name_ar: data.last_name_ar || data.lastNameAr,
  blood_type: data.blood_type || data.bloodType || 'unknown',
  national_id: data.national_id || data.nationalId,
  passport_number: data.passport_number || data.passportNumber,
  address: data.address,
  city: data.city,
  region_id: data.region_id || data.regionId,
  country_id: data.country_id || data.countryId,
  emergency_contact_name: data.emergency_contact_name || data.emergencyContactName,
  emergency_contact_phone:
    data.emergency_contact_phone || data.emergencyContactPhone,
  emergency_contact_relation:
    data.emergency_contact_relation || data.emergencyContactRelation,
  allergies: data.allergies || [],
  chronic_conditions: data.chronic_conditions || data.chronicConditions || [],
  current_medications: (data.current_medications || data.currentMedications || []).map(
    (item) => (typeof item === 'string' ? { name: item } : item)
  ),
  insurance_provider: data.insurance_provider || data.insuranceProvider,
  insurance_number: data.insurance_number || data.insuranceNumber,
  notes: data.notes,
})

const buildDoctorPayload = (data) => ({
  hospital_id: data.hospital_id || data.hospitalId,
  first_name: data.first_name || data.firstName,
  last_name: data.last_name || data.lastName,
  email: data.email,
  password: data.password,
  phone: data.phone,
  specialty: data.specialty,
  license_number: data.license_number || data.licenseNumber,
  employee_id: data.employee_id || data.employeeId,
  first_name_ar: data.first_name_ar || data.firstNameAr,
  last_name_ar: data.last_name_ar || data.lastNameAr,
  gender: data.gender,
  date_of_birth: data.date_of_birth || data.dateOfBirth,
  qualification: data.qualification || data.qualifications,
  years_of_experience: data.years_of_experience || data.yearsOfExperience || 0,
  bio: data.bio,
  country_id: data.country_id || data.countryId,
  region_id: data.region_id || data.regionId,
})

const buildAdminPayload = (data) => ({
  hospital_id: data.hospital_id || data.hospitalId,
  first_name: data.first_name || data.firstName,
  last_name: data.last_name || data.lastName,
  email: data.email,
  password: data.password,
  phone: data.phone,
  department: data.department || 'General',
  employee_id: data.employee_id || data.employeeId,
  country_id: data.country_id || data.countryId,
  region_id: data.region_id || data.regionId,
  role: toBackendRole(data.role) || 'admin',
})

export const AuthProvider = ({ children }) => {
  const [userRole, setUserRole] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [mustResetPassword, setMustResetPassword] = useState(false)
  const [error, setError] = useState(null)

  const cache = useRef({
    countries: null,
    regions: {},
    hospitals: {},
  })

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const handleUserLoad = useCallback(async (apiUser) => {
    const rawRole = String(apiUser?.role || '').trim().toLowerCase()
    const normalizedRole = ROLE_ALIAS_MAP[rawRole] || rawRole || null
    const profile = apiUser?.profile || {}
    const profileId = profile?.id || apiUser?.id
    const authUserId = apiUser?.id

    const fullUser = {
      ...profile,
      id: profileId,
      profile_id: profileId,
      auth_user_id: authUserId,
      user_id: authUserId,
      email: apiUser?.email,
      user_role: normalizedRole,
      photo_url: profile?.photo_url || profile?.avatar_url || null,
      avatar_url: profile?.avatar_url || profile?.photo_url || null,
      _raw_profile: profile,
    }

    setCurrentUser(fullUser)
    setUserRole(normalizedRole)
    setIsAuthenticated(true)
    setMustResetPassword(profile?.must_reset_password === true)

    localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(fullUser))
    if (normalizedRole) {
      localStorage.setItem(USER_ROLE_KEY, normalizedRole)
    } else {
      localStorage.removeItem(USER_ROLE_KEY)
    }
  }, [])

  const handleLogoutCleanup = useCallback(() => {
    localStorage.removeItem(CURRENT_USER_KEY)
    localStorage.removeItem(USER_ROLE_KEY)
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem('biointellect_recovery_token')
    setIsAuthenticated(false)
    setCurrentUser(null)
    setUserRole(null)
    setMustResetPassword(false)
    setError(null)
  }, [])

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem(ACCESS_TOKEN_KEY)

      if (!token) {
        setIsLoading(false)
        return
      }

      try {
        const response = await authAPI.getMe()
        if (response.success && response.data) {
          await handleUserLoad(response.data)
        } else {
          throw new Error('Invalid session data')
        }
      } catch (err) {
        console.error('Auth session initialization failed:', err)
        handleLogoutCleanup()
      } finally {
        setIsLoading(false)
      }
    }

    initAuth()
  }, [handleLogoutCleanup, handleUserLoad])

  const selectRole = useCallback((role) => {
    setUserRole(role)
    localStorage.setItem(USER_ROLE_KEY, role)
  }, [])

  const refreshUser = useCallback(async () => {
    try {
      const response = await authAPI.getMe()
      if (!response.success || !response.data) {
        throw new Error('Failed to refresh user session')
      }

      await handleUserLoad(response.data)
      return { success: true, data: response.data }
    } catch (err) {
      const message = normalizeApiError(err, 'Failed to refresh user session')
      setError(message)
      return { success: false, error: message }
    }
  }, [handleUserLoad])

  const signIn = useCallback(
    async (email, password) => {
      setIsLoading(true)
      clearError()
      try {
        const response = await authAPI.signIn(email, password)
        if (!response.success || !response.session?.access_token) {
          throw new Error(response.message || 'Login failed')
        }

        localStorage.setItem(ACCESS_TOKEN_KEY, response.session.access_token)
        await handleUserLoad(response.user)

        return {
          success: true,
          role:
            ROLE_ALIAS_MAP[String(response.user?.role || '').toLowerCase()] ||
            response.user?.role,
        }
      } catch (err) {
        const message = normalizeApiError(err, 'Login failed')
        console.error('Login error:', err)
        setError(message)
        return { success: false, error: message }
      } finally {
        setIsLoading(false)
      }
    },
    [clearError, handleUserLoad]
  )

  const signOut = useCallback(
    async (scope = 'local') => {
      try {
        if (scope === 'global') {
          await authAPI.signOut(scope)
        }
      } catch (err) {
        console.warn('Global logout notification failed', err)
      } finally {
        if (scope === 'local' || scope === 'global') {
          handleLogoutCleanup()
          window.location.href = '/login'
        }
      }
    },
    [handleLogoutCleanup]
  )

  const signUp = useCallback(
    async (signUpData) => {
      setIsLoading(true)
      clearError()
      try {
        const response = await authAPI.signUp(
          buildPublicSignUpPayload(signUpData, userRole)
        )
        if (!response.success) {
          throw new Error(response.message || 'Registration failed')
        }

        return {
          success: true,
          userId: response.user?.id || response.user_id,
          mrn: response.user?.mrn || response.mrn,
          user: response.user || null,
        }
      } catch (err) {
        const message = normalizeApiError(err, 'Registration failed')
        console.error('Registration error:', err)
        setError(message)
        return { success: false, error: message }
      } finally {
        setIsLoading(false)
      }
    },
    [clearError, userRole]
  )

  const registerPatient = useCallback(
    async (patientData) => {
      setIsLoading(true)
      clearError()
      try {
        const response = await usersAPI.createPatient(buildPatientPayload(patientData))
        const payload = response.data || response
        return {
          success: true,
          userId: payload.user_id || payload.id,
          mrn: payload.mrn,
          data: payload,
        }
      } catch (err) {
        const message = normalizeApiError(err, 'Patient registration failed')
        setError(message)
        return { success: false, error: message }
      } finally {
        setIsLoading(false)
      }
    },
    [clearError]
  )

  const registerDoctor = useCallback(
    async (doctorData) => {
      setIsLoading(true)
      clearError()
      try {
        const response = await usersAPI.createDoctor(buildDoctorPayload(doctorData))
        const payload = response.data || response
        return {
          success: true,
          userId: payload.user_id || payload.id,
          data: payload,
        }
      } catch (err) {
        const message = normalizeApiError(err, 'Doctor registration failed')
        setError(message)
        return { success: false, error: message }
      } finally {
        setIsLoading(false)
      }
    },
    [clearError]
  )

  const registerAdmin = useCallback(
    async (adminData) => {
      setIsLoading(true)
      clearError()
      try {
        const response = await usersAPI.createAdministrator(buildAdminPayload(adminData))
        const payload = response.data || response
        return {
          success: true,
          userId: payload.user_id || payload.id,
          data: payload,
        }
      } catch (err) {
        const message = normalizeApiError(err, 'Administrator registration failed')
        setError(message)
        return { success: false, error: message }
      } finally {
        setIsLoading(false)
      }
    },
    [clearError]
  )

  const updatePatientProfile = useCallback(
    async (updatedData) => {
      setIsLoading(true)
      clearError()
      try {
        await usersAPI.updateProfile(updatedData)
        await refreshUser()
        return { success: true }
      } catch (err) {
        const message = normalizeApiError(err, 'Profile update failed')
        setError(message)
        return { success: false, error: message }
      } finally {
        setIsLoading(false)
      }
    },
    [clearError, refreshUser]
  )

  const resetPassword = useCallback(
    async (email) => {
      setIsLoading(true)
      clearError()
      try {
        const redirectTo = `${window.location.origin}/reset-password`
        await authAPI.resetPassword(email, redirectTo)
        return { success: true }
      } catch (err) {
        const message = normalizeApiError(err, 'Password reset failed')
        setError(message)
        return { success: false, error: message }
      } finally {
        setIsLoading(false)
      }
    },
    [clearError]
  )

  const updatePassword = useCallback(
    async (newPassword, logoutAll = false) => {
      setIsLoading(true)
      clearError()
      try {
        const token =
          localStorage.getItem(ACCESS_TOKEN_KEY) ||
          localStorage.getItem('biointellect_recovery_token')

        if (!token) {
          throw new Error('No valid session or recovery token found.')
        }

        await authAPI.updatePassword(newPassword, token, logoutAll)
        localStorage.removeItem('biointellect_recovery_token')
        return { success: true }
      } catch (err) {
        const message = normalizeApiError(err, 'Password update failed')
        console.error('Password update error:', err)
        setError(message)
        return { success: false, error: message }
      } finally {
        setIsLoading(false)
      }
    },
    [clearError]
  )

  const completeForcedReset = useCallback(
    async (newPassword) => {
      const result = await updatePassword(newPassword, true)
      if (result.success) {
        setMustResetPassword(false)
        setCurrentUser((prev) => {
          if (!prev) return prev
          const updatedUser = { ...prev, must_reset_password: false }
          localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(updatedUser))
          return updatedUser
        })
      }
      return result
    },
    [updatePassword]
  )

  const fetchCountries = useCallback(async () => {
    if (cache.current.countries) return cache.current.countries

    try {
      const { data } = await geographyAPI.getCountries()
      const formatted = data.map((country) => ({
        country_id: country.id,
        country_name: country.country_name_en,
        country_code: country.iso_2 || country.country_code,
        phone_code: country.phone_code,
        flag_url: country.flag_url,
      }))
      cache.current.countries = formatted
      return formatted
    } catch {
      return []
    }
  }, [])

  const fetchRegions = useCallback(async (countryId) => {
    if (!countryId) return []
    if (cache.current.regions[countryId]) return cache.current.regions[countryId]

    try {
      const { data } = await geographyAPI.getRegions(countryId)
      const formatted = data.map((region) => ({
        region_id: region.id,
        region_name: region.region_name_en,
      }))
      cache.current.regions[countryId] = formatted
      return formatted
    } catch {
      return []
    }
  }, [])

  const fetchHospitals = useCallback(async (regionId) => {
    try {
      const { data } = await geographyAPI.getHospitals(regionId)
      return data.map((hospital) => ({
        hospital_id: hospital.id,
        hospital_name: hospital.hospital_name_en,
      }))
    } catch {
      return []
    }
  }, [])

  const value = useMemo(
    () => ({
      userRole,
      currentUser,
      isAuthenticated,
      isLoading,
      error,
      mustResetPassword,
      selectRole,
      signIn,
      signUp,
      signOut,
      clearError,
      refreshUser,
      registerPatient,
      registerDoctor,
      registerAdmin,
      updatePatientProfile,
      resetPassword,
      updatePassword,
      completeForcedReset,
      fetchCountries,
      fetchRegions,
      fetchHospitals,
      CLINICAL_ROLES,
    }),
    [
      userRole,
      currentUser,
      isAuthenticated,
      isLoading,
      error,
      mustResetPassword,
      selectRole,
      signIn,
      signUp,
      signOut,
      clearError,
      refreshUser,
      registerPatient,
      registerDoctor,
      registerAdmin,
      updatePatientProfile,
      resetPassword,
      updatePassword,
      completeForcedReset,
      fetchCountries,
      fetchRegions,
      fetchHospitals,
    ]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export default AuthContext
