import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '@/store/AuthContext'
import { useGeography } from '@/hooks/useGeography'
import { TopBar } from '@/components/layout/TopBar'
import { InputField } from '@/components/ui/InputField'
import { SelectField } from '@/components/ui/SelectField'
import SearchableSelect from '@/components/ui/SearchableSelect'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import { adminOptions } from '@/config/options'
import { validateStrongPassword } from '@/utils/userFormUtils'
import styles from './SignUp.module.css'

export const SignUp = ({ onSignUpSuccess, onLoginClick, onBack }) => {
  const { signUp, isLoading, error, clearError, userRole } = useAuth()
  const {
    countries,
    regions,
    hospitals,
    selectCountry,
    selectRegion
  } = useGeography()

  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'admin',
    employeeId: '',
    department: '',
    countryId: '',
    regionId: '',
    hospitalId: ''
  })
  const [validationErrors, setValidationErrors] = useState({})
  const defaultCountryId = useMemo(() => {
    if (!countries.length) {
      return ''
    }

    return countries.find((country) => country.country_name === 'Egypt')?.country_id || countries[0].country_id
  }, [countries])

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

  const onCountryChange = (e) => {
    const val = e.target.value
    handleInputChange('countryId', val)
    handleInputChange('regionId', '')
    handleInputChange('hospitalId', '')
    selectCountry(val)
  }

  const onRegionChange = (e) => {
    const val = e.target.value
    handleInputChange('regionId', val)
    handleInputChange('hospitalId', '')
    selectRegion(val)
  }

  // Set default country (Egypt) once countries are loaded
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

  const roleOptions = useMemo(() => adminOptions, [])

  const validateForm = () => {
    const errors = {}

    if (!formData.firstName.trim()) errors.firstName = 'First name is required'
    if (!formData.lastName.trim()) errors.lastName = 'Last name is required'

    if (!formData.email.trim()) {
      errors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Invalid email format'
    }

    if (!formData.password) {
      errors.password = 'Password is required'
    } else {
      const passwordError = validateStrongPassword(formData.password)
      if (passwordError) {
        errors.password = passwordError
      }
    }

    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match'
    }

    if (!formData.employeeId.trim()) {
      errors.employeeId = 'Employee ID is required'
    }

    if (!formData.department.trim()) {
      errors.department = 'Department is required'
    }

    if (!formData.hospitalId) errors.hospitalId = 'Clinical hospital selection is required'

    return errors
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    const errors = validateForm()
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors)
      return
    }

    // Prepare data for AuthContext
    // Resolve IDs to Names for DB storage (User Requirement: "Names instead of IDs")
    const selectedCountry = countries.find(c => c.country_id === formData.countryId);
    const selectedRegion = regions.find(r => r.region_id === formData.regionId);
    const selectedHospital = hospitals.find(h => h.hospital_id === formData.hospitalId);

    const signUpData = {
      ...formData,
      first_name: formData.firstName,
      last_name: formData.lastName,
      country: selectedCountry ? selectedCountry.country_name : formData.countryId,
      region: selectedRegion ? selectedRegion.region_name : formData.regionId,
      hospitalName: selectedHospital ? selectedHospital.hospital_name : null
    }

    const result = await signUp(signUpData)

    if (result && result.success) {
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
            <h1 className={styles.title}>Create Account</h1>
            <p className={styles.subtitle}>
              Provision a BioIntellect administrator account with the required operational details.
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
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              error={validationErrors.email}
              required
            />

            <SelectField
              label="System Role"
              value={formData.role}
              onChange={(e) => handleInputChange('role', e.target.value)}
              options={roleOptions}
              error={validationErrors.role}
              required
            />

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <InputField
                label="Employee ID"
                value={formData.employeeId}
                onChange={(e) => handleInputChange('employeeId', e.target.value)}
                error={validationErrors.employeeId}
                required
              />
              <InputField
                label="Department"
                value={formData.department}
                onChange={(e) => handleInputChange('department', e.target.value)}
                error={validationErrors.department}
                required
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <SearchableSelect
                label="Country"
                value={formData.countryId}
                onChange={onCountryChange}
                options={countries.map(c => ({ value: c.country_id, label: c.country_name, flag_url: c.flag_url }))}
                isCountry
                required
              />
              <SearchableSelect
                label="Region"
                value={formData.regionId}
                onChange={onRegionChange}
                options={regions.map(r => ({ value: r.region_id, label: r.region_name }))}
                required
                disabled={!formData.countryId}
              />
            </div>

            <SearchableSelect
              label="Hospital"
              value={formData.hospitalId}
              onChange={(e) => handleInputChange('hospitalId', e.target.value)}
              options={hospitals.map(h => ({ value: h.hospital_id, label: h.hospital_name }))}
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
              Create account
            </AnimatedButton>
          </form>

          <div className={styles.footer}>
            <p>
              Already have an account?{' '}
              <button
                type="button"
                className={styles.loginLink}
                onClick={onLoginClick}
              >
                Sign in
              </button>
            </p>
          </div>
        </motion.div>
      </div >
    </div >
  )
}
