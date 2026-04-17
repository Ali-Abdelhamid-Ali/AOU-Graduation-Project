import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

import { useAuth } from '@/store/AuthContext'
import { InputField } from '@/components/ui/InputField'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import { validateStrongPassword } from '@/utils/userFormUtils'
import { getDashboardHomeRoute } from '@/utils/dashboardRoutes'
import styles from './ForcePasswordReset.module.css'

const REDIRECT_SECONDS = 5

const SuccessOverlay = ({ userRole }) => {
  const [countdown, setCountdown] = useState(REDIRECT_SECONDS)
  const timerRef = useRef(null)

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timerRef.current)
          window.location.href = getDashboardHomeRoute(userRole)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timerRef.current)
  }, [userRole])

  const progress = ((REDIRECT_SECONDS - countdown) / REDIRECT_SECONDS) * 100
  const circumference = 2 * Math.PI * 26

  return (
    <motion.div
      className={styles.overlayBackdrop}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <motion.div
        className={styles.successPopup}
        initial={{ opacity: 0, scale: 0.7, y: 40 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.85, y: -20 }}
        transition={{ type: 'spring', stiffness: 320, damping: 26, delay: 0.05 }}
      >
        {/* Checkmark circle */}
        <motion.div
          className={styles.checkCircle}
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 400, damping: 20, delay: 0.2 }}
        >
          <motion.svg
            width="44"
            height="44"
            viewBox="0 0 44 44"
            fill="none"
            className={styles.checkSvg}
          >
            <motion.path
              d="M10 22 L18 30 L34 14"
              stroke="currentColor"
              strokeWidth="3.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.5, delay: 0.4, ease: 'easeOut' }}
            />
          </motion.svg>
        </motion.div>

        <motion.div
          className={styles.popupContent}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
        >
          <h2 className={styles.popupTitle}>Password Updated</h2>
          <p className={styles.popupSubtitle}>
            Your account is now secured. Redirecting you to your dashboard…
          </p>
        </motion.div>

        {/* Countdown ring */}
        <motion.div
          className={styles.countdownRing}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <svg width="64" height="64" viewBox="0 0 64 64" className={styles.ringSvg}>
            {/* Track */}
            <circle
              cx="32"
              cy="32"
              r="26"
              fill="none"
              stroke="var(--color-border)"
              strokeWidth="4"
            />
            {/* Progress */}
            <motion.circle
              cx="32"
              cy="32"
              r="26"
              fill="none"
              stroke="var(--color-primary)"
              strokeWidth="4"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={circumference - (progress / 100) * circumference}
              transform="rotate(-90 32 32)"
              style={{ transition: 'stroke-dashoffset 0.9s linear' }}
            />
          </svg>
          <span className={styles.countdownNumber}>{countdown}</span>
        </motion.div>

        <p className={styles.countdownLabel}>
          Entering your portal in <strong>{countdown}</strong> second{countdown !== 1 ? 's' : ''}
        </p>

        <button
          className={styles.enterNowBtn}
          onClick={() => {
            clearInterval(timerRef.current)
            window.location.href = getDashboardHomeRoute(userRole)
          }}
        >
          Enter now →
        </button>
      </motion.div>
    </motion.div>
  )
}

export const ForcePasswordReset = () => {
  const { completeForcedReset, signOut, userRole } = useAuth()
  const [formData, setFormData] = useState({
    newPassword: '',
    confirmPassword: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    const passwordError = validateStrongPassword(formData.newPassword)
    if (passwordError) {
      setError(passwordError)
      return
    }

    if (formData.newPassword !== formData.confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    const result = await completeForcedReset(formData.newPassword)

    if (result.success) {
      setLoading(false)
      setSuccess(true)
      return
    }

    setError(result.error || 'Something went wrong. Please try again.')
    setLoading(false)
  }

  return (
    <div className={styles.pageWrapper}>
      <motion.div
        className={styles.resetCard}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className={styles.header}>
          <div className={styles.badge}>SECURITY ALERT</div>
          <h1 className={styles.title}>Mandatory Security Update</h1>
          <p className={styles.subtitle}>
            To protect your medical records, create a new secure password
            before proceeding.
          </p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <InputField
            id="new-password"
            label="New Secure Password"
            type="password"
            value={formData.newPassword}
            onChange={(e) =>
              setFormData({ ...formData, newPassword: e.target.value })
            }
            required
            placeholder="Min 8 chars: A-Z, a-z, 0-9, symbol"
            helperText="Include uppercase, lowercase, a number, and a special character."
            autoComplete="new-password"
          />
          <InputField
            id="confirm-password"
            label="Confirm New Password"
            type="password"
            value={formData.confirmPassword}
            onChange={(e) =>
              setFormData({ ...formData, confirmPassword: e.target.value })
            }
            required
            autoComplete="new-password"
          />

          <AnimatePresence>
            {error && (
              <motion.div
                className={styles.error}
                initial={{ opacity: 0, y: -6, blockSize: 0 }}
                animate={{ opacity: 1, y: 0, blockSize: 'auto' }}
                exit={{ opacity: 0, y: -4, blockSize: 0 }}
                transition={{ duration: 0.2 }}
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          <div className={styles.actions}>
            <AnimatedButton
              type="submit"
              variant="primary"
              fullWidth
              isLoading={loading}
            >
              Update and Continue
            </AnimatedButton>

            <button type="button" className={styles.logoutButton} onClick={signOut}>
              Logout
            </button>
          </div>
        </form>

        <div className={styles.securityInfo}>
          <p>Password requirements:</p>
          <ul>
            <li>Use 8+ characters</li>
            <li>Mix uppercase and lowercase letters</li>
            <li>Include a number and a symbol</li>
          </ul>
        </div>
      </motion.div>

      <AnimatePresence>
        {success && <SuccessOverlay userRole={userRole} />}
      </AnimatePresence>
    </div>
  )
}
