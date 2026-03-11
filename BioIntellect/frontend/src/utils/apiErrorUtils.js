const describeLocation = (location) => {
  if (!Array.isArray(location)) {
    return ''
  }

  const parts = location
    .map((item) => String(item || '').trim())
    .filter(Boolean)

  return parts.length ? parts.join(' > ') : ''
}

const stringifyErrorDetail = (detail) => {
  if (!detail) {
    return ''
  }

  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => stringifyErrorDetail(item))
      .filter(Boolean)
      .join(' ')
      .trim()
  }

  if (typeof detail === 'object') {
    if (typeof detail.msg === 'string') {
      const location = describeLocation(detail.loc)
      return location ? `${location}: ${detail.msg}` : detail.msg
    }

    if (typeof detail.detail === 'string' || Array.isArray(detail.detail)) {
      return stringifyErrorDetail(detail.detail)
    }

    if (typeof detail.message === 'string' || Array.isArray(detail.message)) {
      return stringifyErrorDetail(detail.message)
    }

    if (typeof detail.error === 'string' || Array.isArray(detail.error)) {
      return stringifyErrorDetail(detail.error)
    }
  }

  return ''
}

export const getApiErrorMessage = (error, fallback = 'Request failed.') => {
  const message =
    stringifyErrorDetail(error?.detail) ||
    stringifyErrorDetail(error?.message) ||
    stringifyErrorDetail(error?.error)

  return message || fallback
}

export const normalizeApiErrorPayload = (
  payload,
  fallback = 'Request failed.'
) => {
  if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
    const detail = getApiErrorMessage(payload, fallback)
    return {
      ...payload,
      detail,
      message: detail,
    }
  }

  const detail = getApiErrorMessage({ detail: payload }, fallback)
  return {
    detail,
    message: detail,
  }
}
