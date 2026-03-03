import { describe, expect, it } from 'vitest'
import { specialtyOptions } from '@/config/options'

describe('frontend smoke', () => {
  it('loads shared options config', () => {
    expect(Array.isArray(specialtyOptions)).toBe(true)
    expect(specialtyOptions.length).toBeGreaterThan(0)
  })
})
