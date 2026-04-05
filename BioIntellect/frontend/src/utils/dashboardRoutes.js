import { ROLES, ROLE_ALIAS_MAP } from '@/config/roles'

export const normalizeDashboardRole = (role) => {
  if (!role) return null
  const normalized = String(role).trim().toLowerCase()
  return ROLE_ALIAS_MAP[normalized] || normalized
}

export const getDashboardHomeRoute = (role) => {
  const normalizedRole = normalizeDashboardRole(role)

  if (normalizedRole === ROLES.SUPER_ADMIN) {
    return '/super-admin'
  }

  if (normalizedRole === ROLES.DOCTOR) {
    return '/doctor-dashboard'
  }

  if (normalizedRole === ROLES.ADMIN) {
    return '/admin-dashboard'
  }

  if (normalizedRole === ROLES.PATIENT) {
    return '/patient-dashboard'
  }

  return '/'
}

export default getDashboardHomeRoute
