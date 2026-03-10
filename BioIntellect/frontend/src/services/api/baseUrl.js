const DEFAULT_API_ROOT = 'http://127.0.0.1:8000'

const trimTrailingSlash = (value) => value.replace(/\/+$/, '')

const ensureVersionSuffix = (value) => {
  const normalized = trimTrailingSlash(value)
  return normalized.endsWith('/v1') ? normalized : `${normalized}/v1`
}

export const API_ROOT_URL = trimTrailingSlash(
  import.meta.env.VITE_API_ROOT_URL ||
    import.meta.env.VITE_API_URL ||
    DEFAULT_API_ROOT
).replace(/\/v1$/, '')

export const API_BASE_URL = ensureVersionSuffix(API_ROOT_URL)

export const buildApiUrl = (path) =>
  `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
