import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { TopBar } from '../components/TopBar'
import { InputField } from '../components/InputField'
import { SelectField } from '../components/SelectField'
import { AnimatedButton } from '../components/AnimatedButton'
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

export const SignUp = ({ onSignUpSuccess, onLoginClick }) => {
  const { signUp, isLoading, error, clearError, userRole } = useAuth()
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    password_confirm: '',
    specific_role: '',
    date_of_birth: '',
    gender: '',
  })
  const [validationErrors, setValidationErrors] = useState({})

  // Determine available roles based on main role selection
  const roleOptions = userRole === 'doctor'
    ? [
      { value: 'physician', label: 'Physician' },
      { value: 'cardiologist', label: 'Cardiologist' },
      { value: 'neurologist', label: 'Neurologist' },
      { value: 'administrator', label: 'Administrator' },
    ]
    : [
      { value: 'patient', label: 'Patient' },
    ]

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

    if (!formData.first_name.trim()) errors.first_name = 'First name is required'
    if (!formData.last_name.trim()) errors.last_name = 'Last name is required'

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

    if (formData.password !== formData.password_confirm) {
      errors.password_confirm = 'Passwords do not match'
    }

    if (!formData.specific_role) {
      errors.specific_role = 'Please select a specific role'
    }

    // Patient specific validation
    if (userRole === 'patient') {
      if (!formData.date_of_birth) errors.date_of_birth = 'Date of birth is required'
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
      firstName: formData.first_name,
      lastName: formData.last_name,
      role: formData.specific_role,
      // Optional fields for patient
      dateOfBirth: formData.date_of_birth,
      gender: formData.gender,
    }

    const result = await signUp(signUpData)

    if (result && result.success) {
      setTimeout(() => onSignUpSuccess(), 300)
    }
  }

  return (
    <div className={styles.pageWrapper}>
      <TopBar userRole={userRole} />

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
              Join BioIntellect as a {userRole === 'doctor' ? 'Medical Professional' : 'Patient'}
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
                id="first_name"
                label="First Name"
                placeholder="Ali"
                value={formData.first_name}
                onChange={(e) => handleInputChange('first_name', e.target.value)}
                error={validationErrors.first_name}
                required
              />
              <InputField
                id="last_name"
                label="Last Name"
                placeholder="Abdelhamid"
                value={formData.last_name}
                onChange={(e) => handleInputChange('last_name', e.target.value)}
                error={validationErrors.last_name}
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
              id="specific_role"
              label={userRole === 'doctor' ? 'Specialty / Role' : 'Role'}
              value={formData.specific_role}
              onChange={(e) => handleInputChange('specific_role', e.target.value)}
              options={roleOptions}
              error={validationErrors.specific_role}
              required
              placeholder="Select your specific role"
            />

            {/* Patient Specific Fields */}
            {userRole === 'patient' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <InputField
                  id="date_of_birth"
                  label="Date of Birth"
                  type="date"
                  value={formData.date_of_birth}
                  onChange={(e) => handleInputChange('date_of_birth', e.target.value)}
                  error={validationErrors.date_of_birth}
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
              id="password_confirm"
              label="Confirm Password"
              type="password"
              placeholder="••••••••"
              value={formData.password_confirm}
              onChange={(e) => handleInputChange('password_confirm', e.target.value)}
              error={validationErrors.password_confirm}
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
