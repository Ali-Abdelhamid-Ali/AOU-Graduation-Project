import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { TopBar } from '../components/TopBar'
import { InputField } from '../components/InputField'
import { AnimatedButton } from '../components/AnimatedButton'
import styles from './ResetPassword.module.css'

/**
 * ResetPassword Page
 * 
 * Password recovery interface
 * Features:
 * - Email input for password reset
 * - Reset link sending
 * - Error handling
 * - Loading state
 * - Navigation back to login
 */

export const ResetPassword = ({ onResetSuccess, onBackToLogin }) => {
  const { resetPassword, isLoading, error, clearError, userRole } = useAuth()
  const [email, setEmail] = useState('')
  const [validationError, setValidationError] = useState('')
  const [resetSent, setResetSent] = useState(false)

  const handleEmailChange = (value) => {
    setEmail(value)
    if (validationError) {
      setValidationError('')
    }
    clearError()
  }

  const validateForm = () => {
    if (!email.trim()) {
      setValidationError('Email is required')
      return false
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setValidationError('Invalid email format')
      return false
    }

    return true
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    setValidationError('')
    const result = await resetPassword(email)

    if (result && result.success) {
      setResetSent(true)
    }
  }

  if (resetSent) {
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
            <div className={styles.successState}>
              <div className={styles.icon}>✓</div>
              <h1 className={styles.title}>Reset Link Sent</h1>
              <p className={styles.subtitle}>
                Check your email at <strong>{email}</strong>
              </p>
              <p className={styles.description}>
                It may take a few minutes to arrive or appear in your spam folder (5-10 minutes)
              </p>

              <div className={styles.steps}>
                <h3>Next steps:</h3>
                <ol>
                  <li>Open the email from BioIntellect</li>
                  <li>Click the password reset link</li>
                  <li>Enter a new password</li>
                  <li>Save changes and return to Sign In</li>
                </ol>
              </div>

              <AnimatedButton
                variant="primary"
                size="large"
                fullWidth
                onClick={onBackToLogin}
              >
                Back to Sign In
              </AnimatedButton>

              <button
                className={styles.sendAgainLink}
                onClick={() => {
                  setResetSent(false)
                  setEmail('')
                }}
              >
                Try again with a different email?
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    )
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
          {/* Header */}
          <div className={styles.header}>
            <h1 className={styles.title}>Reset Password</h1>
            <p className={styles.subtitle}>
              Enter your email and we'll send a password reset link
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
            {/* Email Field */}
            <InputField
              id="reset_email"
              label="Email"
              type="email"
              placeholder="example@hospital.com"
              value={email}
              onChange={(e) => handleEmailChange(e.target.value)}
              error={validationError}
              required
            />

            {/* Submit Button */}
            <AnimatedButton
              type="submit"
              variant="primary"
              size="large"
              fullWidth
              isLoading={isLoading}
            >
              Send Reset Link
            </AnimatedButton>
          </form>

          {/* Back to Login Link */}
          <div className={styles.footer}>
            <button
              type="button"
              className={styles.backLink}
              onClick={onBackToLogin}
            >
              ← Back to Sign In
            </button>
          </div>

          {/* Info Box */}
          <div className={styles.infoBox}>
            <p>
              <strong>Tip:</strong> If you don't receive the email, check your spam folder.
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
