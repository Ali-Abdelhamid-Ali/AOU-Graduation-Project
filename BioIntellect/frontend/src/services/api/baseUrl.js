const trimTrailingSlash = (value) => value.replace(/\/+$/, '')

const ensureVersionSuffix = (value) => {
  const normalized = trimTrailingSlash(value)
  return normalized.endsWith('/v1') ? normalized : `${normalized}/v1`
}

const hasText = (value) => typeof value === 'string' && value.trim().length > 0

export const resolveApiBaseInput = () =>
  [
    import.meta.env.VITE_API_URL,
    import.meta.env.VITE_API_ROOT_URL,
    '/api',
  ].find(hasText)?.trim() || '/api'

const rawApiUrl = resolveApiBaseInput()

export const API_ROOT_URL = trimTrailingSlash(rawApiUrl).replace(/\/v1$/, '')
export const API_BASE_URL = ensureVersionSuffix(API_ROOT_URL)

export const buildApiUrl = (path) =>
  `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
