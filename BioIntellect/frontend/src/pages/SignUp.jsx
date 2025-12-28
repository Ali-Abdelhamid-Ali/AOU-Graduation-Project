import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { useGeography } from '../hooks/useGeography'
import { TopBar } from '../components/TopBar'
import { InputField } from '../components/InputField'
import { SelectField } from '../components/SelectField'
import SearchableSelect from '../components/SearchableSelect'
import { AnimatedButton } from '../components/AnimatedButton'
import { specialtyOptions, adminOptions } from '../constants/options'
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
    dateOfBirth: '',
    gender: 'male',
    countryId: '',
    regionId: '',
    hospitalId: ''
  })
  const [validationErrors, setValidationErrors] = useState({})

  // Set default country (Egypt) once countries are loaded
  useEffect(() => {
    if (countries.length > 0 && !formData.countryId) {
      const egypt = countries.find(c => c.country_name === 'Egypt') || countries[0]
      if (egypt) {
        handleInputChange('countryId', egypt.country_id)
        selectCountry(egypt.country_id)
      }
    }
  }, [countries])

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

  // Determine available roles based on main role selection
  const roleOptions = useMemo(() => {
    if (userRole === 'doctor') {
      return specialtyOptions
    }
    if (userRole === 'administrator') {
      return adminOptions
    }
    return adminOptions
  }, [userRole])

  const genderOptions = [
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' },
  ]

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
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters'
    }

    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match'
    }

    if (!formData.hospitalId) errors.hospitalId = 'Clinical hospital selection is required'

    if (userRole === 'patient') {
      if (!formData.dateOfBirth) errors.dateOfBirth = 'Date of birth is required'
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
              Join BioIntellect as a {userRole === 'doctor' ? 'Medical Professional' : 'System Administrator'}
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
              label={userRole === 'doctor' ? 'Specialty' : ['admin', 'administrator', 'super_admin'].includes(userRole) ? 'System Role' : 'Role'}
              value={formData.role}
              onChange={(e) => handleInputChange('role', e.target.value)}
              options={roleOptions}
              error={validationErrors.role}
              required
            />

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

            {userRole === 'doctor' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <InputField
                  label="Medical License #"
                  placeholder="LIC-XXXXX"
                  value={formData.licenseNumber}
                  onChange={(e) => handleInputChange('licenseNumber', e.target.value)}
                  required
                />
                <InputField
                  label="Phone Number"
                  value={formData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                />
              </div>
            )}

            {userRole === 'patient' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <InputField
                  label="Date of Birth"
                  type="date"
                  value={formData.dateOfBirth}
                  onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
                  error={validationErrors.dateOfBirth}
                  required
                />
                <SelectField
                  label="Gender"
                  value={formData.gender}
                  onChange={(e) => handleInputChange('gender', e.target.value)}
                  options={genderOptions}
                  required
                />
              </div>
            )}

            <InputField
              label="Password"
              type="password"
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              error={validationErrors.password}
              required
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
