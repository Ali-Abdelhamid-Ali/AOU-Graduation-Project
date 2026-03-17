import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'

import { useAuth } from '@/store/AuthContext'
import { useGeography } from '@/hooks/useGeography'
import { TopBar } from '@/components/layout/TopBar'
import { InputField } from '@/components/ui/InputField'
import SearchableSelect from '@/components/ui/SearchableSelect'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import { validateStrongPassword } from '@/utils/userFormUtils'
import styles from './SignUp.module.css'

export const SignUp = ({ onSignUpSuccess, onLoginClick, onBack }) => {
  const { signUp, isLoading, error, clearError, userRole } = useAuth()
  const { countries, regions, hospitals, selectCountry, selectRegion } = useGeography()

  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
    role: 'patient',
    countryId: '',
    regionId: '',
    hospitalId: '',
  })
  const [validationErrors, setValidationErrors] = useState({})

  const defaultCountryId = useMemo(() => {
    if (!countries.length) {
      return ''
    }

    return (
      countries.find((country) => country.country_name === 'Egypt')?.country_id ||
      countries[0].country_id
    )
  }, [countries])

  useEffect(() => {
    if (!defaultCountryId || formData.countryId) {
      return
    }

    setFormData((prev) => ({
      ...prev,
      countryId: defaultCountryId,
    }))
    selectCountry(defaultCountryId)
  }, [defaultCountryId, formData.countryId, selectCountry])

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }))

    if (validationErrors[field]) {
      setValidationErrors((prev) => ({
        ...prev,
        [field]: '',
      }))
    }

    clearError()
  }

  const handleCountryChange = (e) => {
    const value = e.target.value
    handleInputChange('countryId', value)
    handleInputChange('regionId', '')
    handleInputChange('hospitalId', '')
    selectCountry(value)
  }

  const handleRegionChange = (e) => {
    const value = e.target.value
    handleInputChange('regionId', value)
    handleInputChange('hospitalId', '')
    selectRegion(value)
  }

  const validateForm = () => {
    const errors = {}

    if (!formData.firstName.trim()) {
      errors.firstName = 'First name is required'
    }

    if (!formData.lastName.trim()) {
      errors.lastName = 'Last name is required'
    }

    if (!formData.email.trim()) {
      errors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Invalid email format'
    }

    if (!formData.countryId) {
      errors.countryId = 'Country is required'
    }

    if (!formData.regionId) {
      errors.regionId = 'Region is required'
    }

    if (!formData.hospitalId) {
      errors.hospitalId = 'Hospital selection is required'
    }

    if (!formData.password) {
      errors.password = 'Password is required'
    } else {
      const passwordError = validateStrongPassword(formData.password)
      if (passwordError) {
        errors.password = passwordError
      }
    }

    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password'
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match'
    }

    return errors
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    const errors = validateForm()
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors)
      return
    }

    const result = await signUp({
      ...formData,
      role: 'patient',
      first_name: formData.firstName,
      last_name: formData.lastName,
      phone: formData.phone,
      hospital_id: formData.hospitalId,
      country_id: formData.countryId,
      region_id: formData.regionId,
    })

    if (result?.success) {
      setTimeout(() => onSignUpSuccess(), 300)
    }
  }

  return (
    <div className={styles.pageWrapper}>
      <TopBar userRole={userRole} onBack={onBack} />

      <div className={styles.container}>
        <motion.div
          className={styles.card}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className={styles.header}>
            <h1 className={styles.title}>Create Patient Account</h1>
            <p className={styles.subtitle}>
              Public registration is available for patients only. Clinical staff
              accounts are provisioned by administrators.
            </p>
          </div>

          {error && (
            <motion.div
              className={styles.alertError}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {error}
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className={styles.form}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <InputField
                label="First Name"
                placeholder="Ali"
                value={formData.firstName}
                onChange={(e) => handleInputChange('firstName', e.target.value)}
                error={validationErrors.firstName}
                required
              />
              <InputField
                label="Last Name"
                placeholder="Abdelhamid"
                value={formData.lastName}
                onChange={(e) => handleInputChange('lastName', e.target.value)}
                error={validationErrors.lastName}
                required
              />
            </div>

            <InputField
              label="Email"
              type="email"
              placeholder="patient@example.com"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              error={validationErrors.email}
              required
            />

            <InputField
              label="Phone Number"
              type="tel"
              placeholder="+20 100 000 0000"
              value={formData.phone}
              onChange={(e) => handleInputChange('phone', e.target.value)}
            />

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <SearchableSelect
                label="Country"
                value={formData.countryId}
                onChange={handleCountryChange}
                options={countries.map((country) => ({
                  value: country.country_id,
                  label: country.country_name,
                  flag_url: country.flag_url,
                }))}
                isCountry
                required
                error={validationErrors.countryId}
              />
              <SearchableSelect
                label="Region"
                value={formData.regionId}
                onChange={handleRegionChange}
                options={regions.map((region) => ({
                  value: region.region_id,
                  label: region.region_name,
                }))}
                required
                disabled={!formData.countryId}
                error={validationErrors.regionId}
              />
            </div>

            <SearchableSelect
              label="Hospital"
              value={formData.hospitalId}
              onChange={(e) => handleInputChange('hospitalId', e.target.value)}
              options={hospitals.map((hospital) => ({
                value: hospital.hospital_id,
                label: hospital.hospital_name,
              }))}
              required
              disabled={!formData.regionId}
              error={validationErrors.hospitalId}
            />

            <InputField
              label="Password"
              type="password"
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              error={validationErrors.password}
              required
              helperText="Use 8+ characters with uppercase, lowercase, a number, and a special character."
            />

            <InputField
              label="Confirm Password"
              type="password"
              value={formData.confirmPassword}
              onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
              error={validationErrors.confirmPassword}
              required
            />

            <AnimatedButton
              type="submit"
              variant="primary"
              size="large"
              fullWidth
              isLoading={isLoading}
            >
              Create patient account
            </AnimatedButton>
          </form>

          <div className={styles.footer}>
            <p>
              Already have an account?{' '}
              <button type="button" className={styles.loginLink} onClick={onLoginClick}>
                Sign in
              </button>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
