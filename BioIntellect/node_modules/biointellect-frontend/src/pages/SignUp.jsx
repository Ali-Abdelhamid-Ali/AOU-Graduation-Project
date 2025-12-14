import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { TopBar } from '../components/TopBar'
import { InputField } from '../components/InputField'
import { AnimatedButton } from '../components/AnimatedButton'
import styles from './SignUp.module.css'
import useDraggable from '../hooks/useDraggable'

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
    full_name: '',
    email: '',
    password: '',
    password_confirm: '',
  })
  const [validationErrors, setValidationErrors] = useState({})
  const cardRef = useRef(null)
  useDraggable(cardRef, 'signup-card')

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }))
    // Clear field error when user starts typing
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

    if (!formData.full_name.trim()) {
      errors.full_name = 'Full name is required'
    } else if (formData.full_name.trim().length < 3) {
      errors.full_name = 'Full name must be at least 3 characters'
    }

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

    if (!formData.password_confirm) {
      errors.password_confirm = 'Password confirmation is required'
    } else if (formData.password !== formData.password_confirm) {
      errors.password_confirm = 'Passwords do not match'
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

    setValidationErrors({})
    // Call mock signUp from context (simulated async)
    const result = await signUp(formData.full_name, formData.email, formData.password, userRole || 'patient')

    if (result && result.success) {
      setTimeout(() => onSignUpSuccess(), 300)
    }
  }

  return (
    <div className={styles.pageWrapper}>
      <TopBar userRole={userRole} />

      <div className={styles.container}>
        <motion.div
          ref={(el) => {
            cardRef.current = el
          }}
          className={styles.card}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* Header */}
          <div className={styles.header}>
            <h1 className={styles.title}>Create Account</h1>
            <p className={styles.subtitle}>
              Join BioIntellect — a clinical-grade health platform
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <motion.div
              className={styles.alertError}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {error}
            </motion.div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className={styles.form}>
            {/* Full Name Field */}
            <InputField
              id="full_name"
              label="Full Name"
              type="text"
              placeholder="Ali Abdelhamid"
              value={formData.full_name}
              onChange={(e) => handleInputChange('full_name', e.target.value)}
              error={validationErrors.full_name}
              required
            />

            {/* Email Field */}
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

            {/* Password Field */}
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

            {/* Confirm Password Field */}
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

            {/* Terms */}
            <div className={styles.termsWrapper}>
              <p className={styles.terms}>
                By creating an account you agree to our{' '}
                <a href="/terms" className={styles.termsLink} target="_blank" rel="noopener noreferrer">
                  Terms of Service
                </a>
              </p>
            </div>

            {/* Submit Button */}
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

          {/* Divider */}
          <div className={styles.divider}>
            <span>or</span>
          </div>

          {/* Login Link */}
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

          {/* Info Box */}

        </motion.div>
      </div>
    </div>
  )
}
