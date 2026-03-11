import { describe, expect, it } from 'vitest'

import {
  formatMedicationListForInput,
  normalizePatientProfileUpdatePayload,
  splitDelimitedValues,
  validateMinimumPassword,
  validateStrongPassword,
} from './userFormUtils'

describe('userFormUtils', () => {
  it('normalizes patient profile update payloads to backend-safe shapes', () => {
    expect(
      normalizePatientProfileUpdatePayload({
        first_name: 'Mina',
        allergies: 'Penicillin, Dust',
        chronic_conditions: 'Diabetes\nHypertension',
        current_medications: 'Metformin, Aspirin',
      })
    ).toEqual({
      first_name: 'Mina',
      allergies: ['Penicillin', 'Dust'],
      chronic_conditions: ['Diabetes', 'Hypertension'],
      current_medications: [{ name: 'Metformin' }, { name: 'Aspirin' }],
    })
  })

  it('formats medication objects for textarea editing without object noise', () => {
    expect(
      formatMedicationListForInput([
        { name: 'Metformin', dose: '500mg' },
        { name: 'Aspirin' },
      ])
    ).toBe('Metformin, Aspirin')
  })

  it('splits comma and newline separated lists while trimming empty values', () => {
    expect(splitDelimitedValues(' one, two \n three ,,')).toEqual([
      'one',
      'two',
      'three',
    ])
  })

  it('validates provisioning passwords against backend minimum length', () => {
    expect(validateMinimumPassword('short', 8)).toBe(
      'Password must be at least 8 characters long.'
    )
    expect(validateMinimumPassword('LongEnough', 8)).toBe('')
  })

  it('validates strong auth passwords against backend complexity rules', () => {
    expect(validateStrongPassword('weakpass')).toBe(
      'Password must include at least one uppercase letter.'
    )
    expect(validateStrongPassword('ValidPass1!')).toBe('')
  })
})
