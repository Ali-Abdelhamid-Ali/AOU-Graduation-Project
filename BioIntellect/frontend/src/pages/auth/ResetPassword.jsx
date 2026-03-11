import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '@/store/AuthContext'
import { TopBar } from '@/components/layout/TopBar'
import { InputField } from '@/components/ui/InputField'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import { validateStrongPassword } from '@/utils/userFormUtils'
import styles from './ResetPassword.module.css'

/**
 * ResetPassword Page
 * 
 * Password recovery interface
 */

export const ResetPassword = ({ onResetSuccess, onBackToLogin, onBack }) => {
  const { resetPassword, updatePassword, isLoading, error, clearError, userRole } = useAuth()

  // View states: 'request' | 'sent' | 'update' | 'complete'
  const [view, setView] = useState('request')
  const [email, setEmail] = useState('')

  const [passwordData, setPasswordData] = useState({
    new_password: '',
    confirm_password: ''
  })
  const [logoutAll, setLogoutAll] = useState(false)

  const [validationError, setValidationError] = useState('')

  // Detect recovery mode from URL hash or search params
  useEffect(() => {
    const checkRecovery = () => {
      const searchParams = new URLSearchParams(window.location.search)
      const hashParams = new URLSearchParams(window.location.hash.substring(1))

      const accessToken = searchParams.get('access_token') || hashParams.get('access_token')
      const type = searchParams.get('type') || hashParams.get('type')

      if (type === 'recovery' || accessToken) {
        console.log('[ResetPassword] Recovery mode detected via URL sensing.')
        if (accessToken) {
          localStorage.setItem('biointellect_access_token', accessToken)
          // Clear hash/params to prevent sticky state on refresh
          window.history.replaceState(null, '', window.location.pathname)
        }
        setView('update')
        return true
      }
      return false
    }

    checkRecovery()
  }, [])

  const handleEmailChange = (value) => {
    setEmail(value)
    if (validationError) setValidationError('')
    clearError()
  }

  const handlePasswordChange = (field, value) => {
    setPasswordData(prev => ({ ...prev, [field]: value }))
    if (validationError) setValidationError('')
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
    if (!validateRequestForm()) return

    const result = await resetPassword(email)
    if (result && result.success) {
      setView('sent')
    }
  }

  const handleUpdateSubmit = async (e) => {
    e.preventDefault()
    if (!validateUpdateForm()) return

    const result = await updatePassword(passwordData.new_password, logoutAll)
    if (result && result.success) {
      setView('complete')
      onResetSuccess?.(result)
      // Optional: auto-login or redirect after delay
    }
  }

  const renderContent = () => {
    switch (view) {
      case 'sent':
        return (
          <div className={styles.successState}>
            <div className={styles.icon}>✓</div>
            <h1 className={styles.title}>Reset Link Sent</h1>
            <p className={styles.subtitle}>Check your email at <strong>{email}</strong></p>
            <p className={styles.description}>It may take a few minutes to arrive. Check your spam folder if you don&apos;t see it.</p>
            <AnimatedButton variant="primary" size="large" fullWidth onClick={onBackToLogin}>Back to Sign In</AnimatedButton>
            <button className={styles.sendAgainLink} onClick={() => setView('request')}>Try again?</button>
          </div>
        )

      case 'update':
        return (
          <>
            <div className={styles.header}>
              <h1 className={styles.title}>New Password</h1>
              <p className={styles.subtitle}>Enter a strong, unique password for your account</p>
            </div>
            {error && <div className={styles.alertError}>{error}</div>}
            <form onSubmit={handleUpdateSubmit} className={styles.form}>
              <InputField
                id="new_password"
                label="New Password"
                type="password"
                placeholder="••••••••••••••••"
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
                placeholder="••••••••••••••••"
                value={passwordData.confirm_password}
                onChange={(e) => handlePasswordChange('confirm_password', e.target.value)}
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
                <label htmlFor="logout_all">Logout from all other devices for security</label>
              </div>
              <AnimatedButton type="submit" variant="primary" size="large" fullWidth isLoading={isLoading}>Update Password</AnimatedButton>
              <div className={styles.footer}>
                <button type="button" className={styles.backLink} onClick={() => setView('request')}>← Start Over</button>
              </div>
            </form>
          </>
        )

      case 'complete':
        return (
          <div className={styles.successState}>
            <div className={styles.icon}>🎉</div>
            <h1 className={styles.title}>Password Updated</h1>
            <p className={styles.subtitle}>Your password has been changed successfully.</p>
            <AnimatedButton variant="primary" size="large" fullWidth onClick={onBackToLogin}>Sign In Now</AnimatedButton>
          </div>
        )

      default:
        return (
          <>
            <div className={styles.header}>
              <h1 className={styles.title}>Reset Password</h1>
              <p className={styles.subtitle}>Enter your email to receive a recovery link</p>
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
              <AnimatedButton type="submit" variant="primary" size="large" fullWidth isLoading={isLoading}>Send Reset Link</AnimatedButton>
            </form>
            <div className={styles.footer}>
              <button type="button" className={styles.backLink} onClick={onBackToLogin}>← Back to Sign In</button>
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
                staggerChildren: 0.08
              }
            }
          }}
        >
          {renderContent()}
          {view === 'request' && (
            <div className={styles.infoBox}>
              <p><strong>Tip:</strong> If you don&apos;t receive the email, check your spam folder.</p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}
