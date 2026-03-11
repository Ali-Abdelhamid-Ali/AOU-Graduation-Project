import { describe, expect, it } from 'vitest'

import {
  getApiErrorMessage,
  normalizeApiErrorPayload,
} from './apiErrorUtils'

describe('apiErrorUtils', () => {
  it('converts FastAPI validation arrays into readable strings', () => {
    expect(
      getApiErrorMessage(
        {
          detail: [
            {
              type: 'string_too_short',
              loc: ['body', 'reason'],
              msg: 'String should have at least 1 character',
            },
          ],
        },
        'fallback'
      )
    ).toBe('body > reason: String should have at least 1 character')
  })

  it('normalizes nested payload objects to string detail fields', () => {
    expect(
      normalizeApiErrorPayload({
        detail: [{ loc: ['body', 'appointment_date'], msg: 'Field required' }],
      })
    ).toEqual({
      detail: 'body > appointment_date: Field required',
      message: 'body > appointment_date: Field required',
    })
  })
})
