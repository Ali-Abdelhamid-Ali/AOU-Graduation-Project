export const LEGACY_THEME_STORAGE_KEY = 'biointellect_theme'

const normalizeSegment = (value, fallback) =>
  String(value || fallback || 'guest').trim().toLowerCase().replace(/\s+/g, '-')

export const getThemeStorageKey = (currentUser, userRole) => {
  const roleSegment = normalizeSegment(currentUser?.user_role || currentUser?.role || userRole, 'guest')
  const userSegment = normalizeSegment(
    currentUser?.auth_user_id || currentUser?.user_id || currentUser?.profile_id || currentUser?.id,
    'guest'
  )

  return `${LEGACY_THEME_STORAGE_KEY}:${roleSegment}:${userSegment}`
}

export const readThemePreference = (storageKey) => {
  if (typeof window === 'undefined') return false

  const scopedPreference = window.localStorage.getItem(storageKey)
  if (scopedPreference === 'dark') return true
  if (scopedPreference === 'light') return false

  const legacyPreference = window.localStorage.getItem(LEGACY_THEME_STORAGE_KEY)
  return legacyPreference === 'dark'
}

export const writeThemePreference = (storageKey, isDark) => {
  if (typeof window === 'undefined') return

  window.localStorage.setItem(storageKey, isDark ? 'dark' : 'light')
}