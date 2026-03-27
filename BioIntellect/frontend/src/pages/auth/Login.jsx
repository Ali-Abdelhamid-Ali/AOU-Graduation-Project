import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import anime from 'animejs'

import { useAuth } from '@/store/AuthContext'
import { TopBar } from '@/components/layout/TopBar'
import { InputField } from '@/components/ui/InputField'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import { useSlideInAnimation } from '@/hooks/useAnimations'
import styles from './Login.module.css'

export const Login = ({
  onLoginSuccess,
  onSignUpClick,
  onForgotPasswordClick,
  onBack,
}) => {
  const { signIn, isLoading, error, clearError, userRole } = useAuth()
  const formRef = useSlideInAnimation(true, 'up')
  const errorRef = useRef(null)

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  })
  const [validationErrors, setValidationErrors] = useState({})

  useEffect(() => {
    if (error && errorRef.current) {
      anime({
        targets: errorRef.current,
        translateX: [
          { value: -5, duration: 100 },
          { value: 5, duration: 100 },
          { value: -5, duration: 100 },
          { value: 0, duration: 100 },
        ],
        duration: 500,
        easing: 'linear',
      })
    }
  }, [error])

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

    if (!formData.email.trim()) {
      errors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Invalid email format'
    }

    if (!formData.password) {
      errors.password = 'Password is required'
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
    const result = await signIn(formData.email, formData.password)

    if (result.success) {
      setTimeout(() => {
        onLoginSuccess(result.role)
      }, 500)
    }
  }

  const isPatientPortal = userRole === 'patient'

  return (
    <div className={styles.pageWrapper}>
      <TopBar userRole={userRole} onBack={onBack} />

      <div className={styles.container}>
        <motion.div
          ref={formRef}
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
          <div className={styles.header}>
            <h1 className={styles.title}>
              {isPatientPortal ? 'Patient Portal' : 'Medical Staff Portal'}
            </h1>
            <p className={styles.subtitle}>
              {isPatientPortal
                ? 'Sign in to review your records, appointments, and AI-assisted results.'
                : 'Enter your clinical credentials to access BioIntellect.'}
            </p>
          </div>

          {error && (
            <motion.div
              ref={errorRef}
              className={styles.alertError}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {error}
            </motion.div>
          )}

          <form onSubmit={handleSubmit} className={styles.form}>
            <InputField
              id="email"
              label="Email"
              type="email"
              placeholder="example@hospital.com"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              error={validationErrors.email}
              required
              autoComplete="username"
            />

            <InputField
              id="password"
              label="Password"
              type="password"
              placeholder="Enter your password"
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              error={validationErrors.password}
              required
              autoComplete="current-password"
            />

            <div className={styles.forgotPasswordWrapper}>
              <button
                type="button"
                className={styles.forgotPasswordLink}
                onClick={onForgotPasswordClick}
              >
                Forgot password?
              </button>
            </div>

            <AnimatedButton
              type="submit"
              variant="primary"
              size="large"
              fullWidth
              isLoading={isLoading}
            >
              Sign In
            </AnimatedButton>
          </form>

          <div className={styles.divider}>
            <span>or</span>
          </div>

          <div className={styles.footer}>
            {isPatientPortal ? (
              <p>
                Need a patient account?{' '}
                <button
                  type="button"
                  className={styles.signUpLink}
                  onClick={onSignUpClick}
                >
                  Create one now
                </button>
              </p>
            ) : (
              <p>
                Don&apos;t have an account? Contact your administrator for secure
                provisioning.
              </p>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
