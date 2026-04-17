const LEGACY_ACCESS_TOKEN_KEY = 'biointellect_access_token'
const RECOVERY_TOKEN_KEY = 'biointellect_recovery_token'

let accessToken = null
let accessTokenExpiresAt = null
let recoveryToken = null
let authFailureHandler = null

const getStorage = (kind) => {
  if (typeof window === 'undefined') {
    return null
  }

  return kind === 'session' ? window.sessionStorage : window.localStorage
}

const normalizeExpiry = (expiresAt) => {
  if (!expiresAt) {
    return null
  }

  if (typeof expiresAt === 'number') {
    return expiresAt > 1_000_000_000_000 ? expiresAt : expiresAt * 1000
  }

  const parsed = new Date(expiresAt).getTime()
  return Number.isFinite(parsed) ? parsed : null
}

export const clearPersistedSensitiveTokens = () => {
  const local = getStorage('local')
  const session = getStorage('session')

  local?.removeItem(LEGACY_ACCESS_TOKEN_KEY)
  local?.removeItem(RECOVERY_TOKEN_KEY)
  session?.removeItem(LEGACY_ACCESS_TOKEN_KEY)
}

export const setAccessSession = ({ accessToken: nextAccessToken, expiresAt }) => {
  accessToken = nextAccessToken || null
  accessTokenExpiresAt = accessToken ? normalizeExpiry(expiresAt) : null
  clearPersistedSensitiveTokens()
}

export const clearAccessSession = () => {
  accessToken = null
  accessTokenExpiresAt = null
}

export const getAccessToken = () => accessToken

export const getAccessTokenExpiresAt = () => accessTokenExpiresAt

export const isAccessTokenExpiringSoon = (bufferMs = 60_000) => {
  // If there is no token or no known expiry, treat it as expired so the
  // interceptor triggers a refresh rather than sending a stale/missing token.
  if (!accessToken || !accessTokenExpiresAt) {
    return true
  }

  return accessTokenExpiresAt - Date.now() <= bufferMs
}

export const setRecoveryToken = (token) => {
  recoveryToken = token || null
  const storage = getStorage('session')

  if (!storage) {
    return
  }

  if (recoveryToken) {
    storage.setItem(RECOVERY_TOKEN_KEY, recoveryToken)
  } else {
    storage.removeItem(RECOVERY_TOKEN_KEY)
  }
}

export const getRecoveryToken = () => {
  if (recoveryToken) {
    return recoveryToken
  }

  const storage = getStorage('session')
  recoveryToken = storage?.getItem(RECOVERY_TOKEN_KEY) || null
  return recoveryToken
}

export const clearRecoveryToken = () => {
  recoveryToken = null
  const storage = getStorage('session')
  storage?.removeItem(RECOVERY_TOKEN_KEY)
}

export const registerAuthFailureHandler = (handler) => {
  authFailureHandler = handler

  return () => {
    if (authFailureHandler === handler) {
      authFailureHandler = null
    }
  }
}

export const notifyAuthFailure = async () => {
  if (typeof authFailureHandler === 'function') {
    await authFailureHandler()
  }
}

clearPersistedSensitiveTokens()
