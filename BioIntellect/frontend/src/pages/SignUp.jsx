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

/**
 * SignUp Page
 * 
 * User registration interface
 * Features:
 * - Full name, email, password fields
 * - Form validation
 * - Schema-aligned field names (matching Supabase users table)
 * - Error handling
 * - Loading state
 * - Login link
 */

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
    role: 'patient',
    dateOfBirth: '',
    gender: '',
    countryId: '',
    countryCode: '',
    countryName: '',
    regionId: '',
    regionName: '',
    hospitalId: ''
  })
  const [validationErrors, setValidationErrors] = useState({})

  // Set default country (Egypt) once countries are loaded
  useEffect(() => {
    if (countries.length > 0 && !formData.countryId) {
      const defaultCountry = countries.find(c => c.country_name === 'Egypt') || countries[0]
      handleInputChange('countryId', defaultCountry.country_id)
      handleInputChange('countryCode', defaultCountry.country_code)
      handleInputChange('countryName', defaultCountry.country_name)
      selectCountry(defaultCountry.country_id)
    }
  }, [countries])

  const onCountryChange = (e) => {
    const selected = countries.find(c => c.country_id === e.target.value)
    handleInputChange('countryId', e.target.value)
    handleInputChange('countryCode', selected?.country_code || '')
    handleInputChange('countryName', selected?.country_name || '')
    selectCountry(e.target.value)
  }

  const onRegionChange = (e) => {
    const selected = regions.find(r => r.region_id === e.target.value)
    handleInputChange('regionId', e.target.value)
    handleInputChange('regionName', selected?.region_name || '')
    selectRegion(e.target.value)
  }

  // Determine available roles based on main role selection
  const roleOptions = useMemo(() => {
    if (userRole === 'doctor') {
      return specialtyOptions.filter(opt =>
        !['administrator', 'mini_administrator'].includes(opt.value)
      )
    }
    if (userRole === 'administrator') {
      return adminOptions
    }
    return [{ value: 'patient', label: 'Patient' }]
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

    // Patient specific validation
    if (userRole === 'patient') {
      if (!formData.dateOfBirth) errors.dateOfBirth = 'Date of birth is required'
      if (!formData.gender) errors.gender = 'Gender is required'
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
    const signUpData = {
      email: formData.email,
      password: formData.password,
      first_name: formData.firstName,
      last_name: formData.lastName,
      role: formData.role,
      date_of_birth: formData.dateOfBirth,
      gender: formData.gender,
      phone: formData.phone,
      licenseNumber: formData.licenseNumber,
      hospitalId: formData.hospitalId,
      countryId: formData.countryId,
      regionId: formData.regionId
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
              Join BioIntellect as a {userRole === 'doctor' ? 'Medical Professional' : userRole === 'administrator' ? 'System Administrator' : 'Patient'}
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
            {/* Name Fields Row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <InputField
                id="firstName"
                label="First Name"
                placeholder="Ali"
                value={formData.firstName}
                onChange={(e) => handleInputChange('firstName', e.target.value)}
                error={validationErrors.firstName}
                required
              />
              <InputField
                id="lastName"
                label="Last Name"
                placeholder="Abdelhamid"
                value={formData.lastName}
                onChange={(e) => handleInputChange('lastName', e.target.value)}
                error={validationErrors.lastName}
                required
              />
            </div>

            <InputField
              id="email"
              label="Email"
              type="email"
              placeholder="example@hospital.com"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              error={validationErrors.email}
              required
            />

            {/* Role Dropdown */}
            <SelectField
              id="role"
              label={userRole === 'doctor' ? 'Specialty / Role' : userRole === 'administrator' ? 'System Role' : 'Role'}
              value={formData.role}
              onChange={(e) => handleInputChange('role', e.target.value)}
              options={roleOptions}
              error={validationErrors.role}
              required
              placeholder="Select your specific role"
            />

            {/* Clinical Location Row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <SearchableSelect
                id="countryId"
                label="Country"
                value={formData.countryId}
                onChange={onCountryChange}
                options={countries.map(c => ({
                  value: c.country_id,
                  label: c.country_name,
                  code: c.country_code
                }))}
                required
                isCountry={true}
                placeholder="Search for your country..."
              />
              <SearchableSelect
                id="regionId"
                label="Region / State"
                value={formData.regionId}
                onChange={onRegionChange}
                options={regions.map(r => ({ value: r.region_id, label: r.region_name }))}
                required
                disabled={!formData.countryId}
                placeholder={!formData.countryId ? "Select country first" : "Search regions..."}
              />
            </div>

            <SearchableSelect
              id="hospitalId"
              label="Assigned Clinical Hospital"
              value={formData.hospitalId}
              onChange={(e) => handleInputChange('hospitalId', e.target.value)}
              options={hospitals.map(h => ({ value: h.hospital_id, label: h.hospital_name }))}
              required
              disabled={!formData.regionId}
              error={validationErrors.hospitalId}
              placeholder={!formData.regionId ? "Select region first" : "Search hospitals..."}
            />

            {/* Doctor Specific Fields */}
            {userRole === 'doctor' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <InputField
                  id="licenseNumber"
                  label="Medical License #"
                  placeholder="LIC-XXXXX"
                  value={formData.licenseNumber}
                  onChange={(e) => handleInputChange('licenseNumber', e.target.value)}
                  error={validationErrors.licenseNumber}
                  required
                />
                <InputField
                  id="phone"
                  label="Phone Number"
                  placeholder="+20 1XX..."
                  value={formData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                />
              </div>
            )}

            {/* Patient Specific Fields */}
            {userRole === 'patient' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <InputField
                  id="dateOfBirth"
                  label="Date of Birth"
                  type="date"
                  value={formData.dateOfBirth}
                  onChange={(e) => handleInputChange('dateOfBirth', e.target.value)}
                  error={validationErrors.dateOfBirth}
                  required
                />
                <SelectField
                  id="gender"
                  label="Gender"
                  value={formData.gender}
                  onChange={(e) => handleInputChange('gender', e.target.value)}
                  options={genderOptions}
                  error={validationErrors.gender}
                  required
                  placeholder="Select gender"
                />
              </div>
            )}

            <InputField
              id="password"
              label="Password"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              error={validationErrors.password}
              required
              helperText="Use at least 6 characters"
            />

            <InputField
              id="confirmPassword"
              label="Confirm Password"
              type="password"
              placeholder="••••••••"
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
      </div>
    </div>
  )
}
