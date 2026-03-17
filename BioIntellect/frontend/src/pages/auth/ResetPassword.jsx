import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

import { useAuth } from '@/store/AuthContext'
import { TopBar } from '@/components/layout/TopBar'
import { InputField } from '@/components/ui/InputField'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import { validateStrongPassword } from '@/utils/userFormUtils'
import {
  clearPersistedSensitiveTokens,
  setRecoveryToken,
} from '@/services/auth/sessionStore'
import styles from './ResetPassword.module.css'

export const ResetPassword = ({ onResetSuccess, onBackToLogin, onBack }) => {
  const { resetPassword, updatePassword, isLoading, error, clearError, userRole } =
    useAuth()

  const [view, setView] = useState('request')
  const [email, setEmail] = useState('')
  const [passwordData, setPasswordData] = useState({
    new_password: '',
    confirm_password: '',
  })
  const [logoutAll, setLogoutAll] = useState(false)
  const [validationError, setValidationError] = useState('')

  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search)
    const hashParams = new URLSearchParams(window.location.hash.substring(1))
    const accessToken =
      searchParams.get('access_token') || hashParams.get('access_token')
    const type = searchParams.get('type') || hashParams.get('type')

    if (type === 'recovery' || accessToken) {
      if (accessToken) {
        clearPersistedSensitiveTokens()
        setRecoveryToken(accessToken)
        window.history.replaceState(null, '', window.location.pathname)
      }
      setView('update')
    }
  }, [])

  const handleEmailChange = (value) => {
    setEmail(value)
    if (validationError) {
      setValidationError('')
    }
    clearError()
  }

  const handlePasswordChange = (field, value) => {
    setPasswordData((prev) => ({ ...prev, [field]: value }))
    if (validationError) {
      setValidationError('')
    }
    clearError()
  }

  const validateRequestForm = () => {
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

  const validateUpdateForm = () => {
    const { new_password, confirm_password } = passwordData

    const passwordError = validateStrongPassword(new_password)
    if (passwordError) {
      setValidationError(passwordError)
      return false
    }

    if (new_password !== confirm_password) {
      setValidationError('Passwords do not match')
      return false
    }

    return true
  }

  const handleRequestSubmit = async (e) => {
    e.preventDefault()
    if (!validateRequestForm()) {
      return
    }

    const result = await resetPassword(email)
    if (result?.success) {
      setView('sent')
    }
  }

  const handleUpdateSubmit = async (e) => {
    e.preventDefault()
    if (!validateUpdateForm()) {
      return
    }

    const result = await updatePassword(passwordData.new_password, logoutAll)
    if (result?.success) {
      setView('complete')
      onResetSuccess?.(result)
    }
  }

  const renderContent = () => {
    switch (view) {
      case 'sent':
        return (
          <div className={styles.successState}>
            <div className={styles.icon}>OK</div>
            <h1 className={styles.title}>Reset Link Sent</h1>
            <p className={styles.subtitle}>
              Check your email at <strong>{email}</strong>
            </p>
            <p className={styles.description}>
              It may take a few minutes to arrive. Check your spam folder if you
              do not see it.
            </p>
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
              onClick={() => setView('request')}
            >
              Try again?
            </button>
          </div>
        )

      case 'update':
        return (
          <>
            <div className={styles.header}>
              <h1 className={styles.title}>New Password</h1>
              <p className={styles.subtitle}>
                Enter a strong, unique password for your account
              </p>
            </div>
            {error && <div className={styles.alertError}>{error}</div>}
            <form onSubmit={handleUpdateSubmit} className={styles.form}>
              <InputField
                id="new_password"
                label="New Password"
                type="password"
                placeholder="Create a new password"
                value={passwordData.new_password}
                onChange={(e) => handlePasswordChange('new_password', e.target.value)}
                error={validationError}
                required
                helperText="Use 8+ characters with uppercase, lowercase, a number, and a special character."
                autoComplete="new-password"
              />
              <InputField
                id="confirm_password"
                label="Confirm New Password"
                type="password"
                placeholder="Repeat the new password"
                value={passwordData.confirm_password}
                onChange={(e) =>
                  handlePasswordChange('confirm_password', e.target.value)
                }
                required
                autoComplete="new-password"
              />
              <div className={styles.checkboxGroup}>
                <input
                  type="checkbox"
                  id="logout_all"
                  checked={logoutAll}
                  onChange={(e) => setLogoutAll(e.target.checked)}
                />
                <label htmlFor="logout_all">
                  Log out all other devices for security
                </label>
              </div>
              <AnimatedButton
                type="submit"
                variant="primary"
                size="large"
                fullWidth
                isLoading={isLoading}
              >
                Update Password
              </AnimatedButton>
              <div className={styles.footer}>
                <button
                  type="button"
                  className={styles.backLink}
                  onClick={() => setView('request')}
                >
                  {'<-'} Start Over
                </button>
              </div>
            </form>
          </>
        )

      case 'complete':
        return (
          <div className={styles.successState}>
            <div className={styles.icon}>OK</div>
            <h1 className={styles.title}>Password Updated</h1>
            <p className={styles.subtitle}>
              Your password has been changed successfully.
            </p>
            <AnimatedButton
              variant="primary"
              size="large"
              fullWidth
              onClick={onBackToLogin}
            >
              Sign In Now
            </AnimatedButton>
          </div>
        )

      default:
        return (
          <>
            <div className={styles.header}>
              <h1 className={styles.title}>Reset Password</h1>
              <p className={styles.subtitle}>
                Enter your email to receive a recovery link
              </p>
            </div>
            {error && <div className={styles.alertError}>{error}</div>}
            <form onSubmit={handleRequestSubmit} className={styles.form}>
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
            <div className={styles.footer}>
              <button
                type="button"
                className={styles.backLink}
                onClick={onBackToLogin}
              >
                {'<-'} Back to Sign In
              </button>
            </div>
          </>
        )
    }
  }

  return (
    <div className={styles.pageWrapper}>
      <TopBar userRole={userRole} onBack={onBack} />
      <div className={styles.container}>
        <motion.div
          className={styles.card}
          initial="hidden"
          animate="visible"
          variants={{
            hidden: { opacity: 0, y: 30, scale: 0.98 },
            visible: {
              opacity: 1,
              y: 0,
              scale: 1,
              transition: {
                duration: 0.5,
                ease: [0.22, 1, 0.36, 1],
                staggerChildren: 0.08,
              },
            },
          }}
        >
          {renderContent()}
          {view === 'request' && (
            <div className={styles.infoBox}>
              <p>
                <strong>Tip:</strong> If you do not receive the email, check your
                spam folder.
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
