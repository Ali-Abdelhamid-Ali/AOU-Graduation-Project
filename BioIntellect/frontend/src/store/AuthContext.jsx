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
import {
  clearAccessSession,
  clearPersistedSensitiveTokens,
  clearRecoveryToken,
  getAccessToken,
  getRecoveryToken,
  registerAuthFailureHandler,
  setAccessSession,
} from '@/services/auth/sessionStore'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import { ROLES, CLINICAL_ROLES, ROLE_ALIAS_MAP, normalizeRole } from '@/config/roles'
import {
  normalizeMedicationList,
  normalizePatientProfileUpdatePayload,
  splitDelimitedValues,
} from '@/utils/userFormUtils'

const AUTH_CONTEXT_GLOBAL_KEY = '__biointellect_auth_context__'

const buildAuthFallback = () => ({
  userRole: null,
  currentUser: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  mustResetPassword: false,
  selectRole: () => {},
  signIn: async () => ({ success: false, error: 'Auth provider unavailable' }),
  signUp: async () => ({ success: false, error: 'Auth provider unavailable' }),
  signOut: async () => {},
  clearError: () => {},
  refreshUser: async () => ({ success: false, error: 'Auth provider unavailable' }),
  registerPatient: async () => ({ success: false, error: 'Auth provider unavailable' }),
  registerDoctor: async () => ({ success: false, error: 'Auth provider unavailable' }),
  registerAdmin: async () => ({ success: false, error: 'Auth provider unavailable' }),
  updatePatientProfile: async () => ({ success: false, error: 'Auth provider unavailable' }),
  resetPassword: async () => ({ success: false, error: 'Auth provider unavailable' }),
  updatePassword: async () => ({ success: false, error: 'Auth provider unavailable' }),
  completeForcedReset: async () => ({ success: false, error: 'Auth provider unavailable' }),
  fetchCountries: async () => [],
  fetchRegions: async () => [],
  fetchHospitals: async () => [],
  CLINICAL_ROLES,
})

const globalScope = typeof window !== 'undefined' ? window : globalThis
const authFallback = buildAuthFallback()

const AuthContext =
  globalScope[AUTH_CONTEXT_GLOBAL_KEY] || createContext(authFallback)

if (!globalScope[AUTH_CONTEXT_GLOBAL_KEY]) {
  globalScope[AUTH_CONTEXT_GLOBAL_KEY] = AuthContext
}

const normalizeApiError = (err, fallback) => getApiErrorMessage(err, fallback)

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
  allergies: splitDelimitedValues(data.allergies || []),
  chronic_conditions: splitDelimitedValues(
    data.chronic_conditions || data.chronicConditions || []
  ),
  current_medications: normalizeMedicationList(
    data.current_medications || data.currentMedications || []
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

  const applySessionPayload = useCallback((session) => {
    if (!session?.access_token) {
      throw new Error('Invalid session payload received from the API.')
    }

    setAccessSession({
      accessToken: session.access_token,
      expiresAt: session.expires_at,
    })
  }, [])

  const handleUserLoad = useCallback(async (apiUser) => {
    const rawRole = String(apiUser?.role || '').trim().toLowerCase()
    const normalizedRole = ROLE_ALIAS_MAP[rawRole] || rawRole || null
    const profile = apiUser?.profile || {}
    const profileId = profile?.id || apiUser?.id
    const authUserId = apiUser?.id
    const resolvedAvatar =
      apiUser?.avatar_url ||
      apiUser?.photo_url ||
      profile?.avatar_url ||
      profile?.photo_url ||
      null

    const fullUser = {
      ...profile,
      id: profileId,
      profile_id: profileId,
      auth_user_id: authUserId,
      user_id: authUserId,
      email: apiUser?.email,
      user_role: normalizedRole,
      photo_url: resolvedAvatar,
      avatar_url: resolvedAvatar,
      _raw_profile: profile,
    }

    setCurrentUser(fullUser)
    setUserRole(normalizedRole)
    setIsAuthenticated(true)
    setMustResetPassword(profile?.must_reset_password === true)
  }, [])

  const handleLogoutCleanup = useCallback(() => {
    clearAccessSession()
    clearRecoveryToken()
    clearPersistedSensitiveTokens()
    setIsAuthenticated(false)
    setCurrentUser(null)
    setUserRole(null)
    setMustResetPassword(false)
    setError(null)
  }, [])

  useEffect(() => {
    const unregisterAuthFailureHandler = registerAuthFailureHandler(async () => {
      handleLogoutCleanup()
    })

    return unregisterAuthFailureHandler
  }, [handleLogoutCleanup])

  useEffect(() => {
    let isMounted = true

    const initAuth = async () => {
      try {
        let userPayload = null

        const refreshResponse = await authAPI.refresh()

        if (refreshResponse?.success && refreshResponse?.session?.access_token) {
          applySessionPayload(refreshResponse.session)
          userPayload = refreshResponse.user || null
        } else if (!getAccessToken()) {
          throw new Error(refreshResponse?.message || 'Unable to restore the session')
        }

        if (!userPayload) {
          const response = await authAPI.getMe()
          if (!response.success || !response.data) {
            throw new Error('Invalid session data')
          }
          userPayload = response.data
        }

        if (!isMounted) return

        if (userPayload) {
          await handleUserLoad(userPayload)
        } else {
          throw new Error('Authenticated session did not include a user payload')
        }
      } catch (err) {
        if (!isMounted) return
        console.error('Auth session initialization failed:', err)
        handleLogoutCleanup()
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    initAuth()

    return () => {
      isMounted = false
    }
  }, [applySessionPayload, handleLogoutCleanup, handleUserLoad])

  const selectRole = useCallback((role) => {
    setUserRole(role)
  }, [])

  const refreshUser = useCallback(async () => {
    try {
      const refreshResponse = await authAPI.refresh()

      if (refreshResponse?.success && refreshResponse?.user) {
        if (refreshResponse?.session?.access_token) {
          applySessionPayload(refreshResponse.session)
        }

        await handleUserLoad(refreshResponse.user)
        return { success: true, data: refreshResponse.user }
      }

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
  }, [applySessionPayload, handleUserLoad])

  const signIn = useCallback(
    async (email, password) => {
      setIsLoading(true)
      clearError()
      try {
        const response = await authAPI.signIn(email, password)
        if (!response.success || !response.session?.access_token) {
          throw new Error(response.message || 'Login failed')
        }

        clearRecoveryToken()
        applySessionPayload(response.session)
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
    [applySessionPayload, clearError, handleUserLoad]
  )

  const signOut = useCallback(
    async (scope = 'local') => {
      try {
        await authAPI.signOut(scope)
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
        const response = await usersAPI.updateProfile(
          normalizePatientProfileUpdatePayload(updatedData)
        )
        const updatedProfile = response?.data

        if (updatedProfile) {
          setCurrentUser((prev) => {
            if (!prev) return prev

            const nextUser = {
              ...prev,
              ...updatedProfile,
              id: updatedProfile.id ?? prev.id,
              profile_id: updatedProfile.id ?? prev.profile_id,
              user_id: updatedProfile.user_id ?? prev.user_id,
              auth_user_id: prev.auth_user_id ?? updatedProfile.user_id ?? prev.user_id,
            }
            return nextUser
          })
        }

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
    async (newPassword, logoutAll = false, currentPassword) => {
      setIsLoading(true)
      clearError()
      try {
        const token = getAccessToken() || getRecoveryToken()

        if (!token) {
          throw new Error('No valid session or recovery token found.')
        }

        await authAPI.updatePassword(
          newPassword,
          token,
          logoutAll,
          currentPassword
        )
        clearRecoveryToken()
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
          return { ...prev, must_reset_password: false }
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
  if (!context || context === authFallback) {
    const message = 'useAuth must be used within AuthProvider'
    if (import.meta.env?.DEV) {
      console.error(message)
      return authFallback
    }
    throw new Error(message)
  }
  return context
}

export default AuthContext
