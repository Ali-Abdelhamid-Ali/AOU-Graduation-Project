const normalizeString = (value) =>
  typeof value === 'string' ? value.trim() : ''

export const formatListForInput = (value) => {
  if (Array.isArray(value)) {
    return value
      .map((item) => normalizeString(item))
      .filter(Boolean)
      .join(', ')
  }

  return typeof value === 'string' ? value : ''
}

export const splitDelimitedValues = (value) => {
  if (Array.isArray(value)) {
    return value
      .map((item) => normalizeString(item))
      .filter(Boolean)
  }

  if (typeof value !== 'string') {
    return []
  }

  return value
    .split(/[\n,]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

const normalizeMedication = (value) => {
  if (typeof value === 'string') {
    const name = value.trim()
    return name ? { name } : null
  }

  if (!value || typeof value !== 'object') {
    return null
  }

  const name = normalizeString(value.name)
  if (!name) {
    return null
  }

  return {
    ...value,
    name,
  }
}

export const normalizeMedicationList = (value) => {
  if (Array.isArray(value)) {
    return value.map(normalizeMedication).filter(Boolean)
  }

  return splitDelimitedValues(value).map((name) => ({ name }))
}

export const formatMedicationListForInput = (value) =>
  normalizeMedicationList(value)
    .map((item) => item.name)
    .join(', ')

export const normalizePatientProfileUpdatePayload = (payload = {}) => {
  const normalized = { ...payload }

  if (Object.prototype.hasOwnProperty.call(normalized, 'allergies')) {
    normalized.allergies = splitDelimitedValues(normalized.allergies)
  }

  if (Object.prototype.hasOwnProperty.call(normalized, 'chronic_conditions')) {
    normalized.chronic_conditions = splitDelimitedValues(
      normalized.chronic_conditions
    )
  }

  if (Object.prototype.hasOwnProperty.call(normalized, 'current_medications')) {
    normalized.current_medications = normalizeMedicationList(
      normalized.current_medications
    )
  }

  return normalized
}

export const validateMinimumPassword = (password, minLength = 8) => {
  if (!password) {
    return 'Password is required.'
  }

  if (String(password).length < minLength) {
    return `Password must be at least ${minLength} characters long.`
  }

  return ''
}

export const validateStrongPassword = (password) => {
  const minimumLengthError = validateMinimumPassword(password, 8)
  if (minimumLengthError) {
    return minimumLengthError
  }

  if (!/[A-Z]/.test(password)) {
    return 'Password must include at least one uppercase letter.'
  }

  if (!/[a-z]/.test(password)) {
    return 'Password must include at least one lowercase letter.'
  }

  if (!/\d/.test(password)) {
    return 'Password must include at least one number.'
  }

  if (!/[^\w\s]/.test(password)) {
    return 'Password must include at least one special character.'
  }

  return ''
}
