import { motion } from 'framer-motion'

import { TopBar } from '@/components/layout/TopBar'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import { useAuth } from '@/store/AuthContext'
import styles from './ResetPassword.module.css'

export const EmailConfirmation = ({ onSignInClick }) => {
  const { userRole } = useAuth()

  return (
    <div className={styles.pageWrapper}>
      <TopBar userRole={userRole} />

      <div className={styles.container}>
        <motion.div
          className={styles.card}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          style={{ textAlign: 'center' }}
        >
          <div className={styles.confirmationIcon}>
            OK
          </div>

          <h1 className={styles.title}>Account Ready</h1>
          <p className={`${styles.subtitle} ${styles.confirmationSubtitle}`}>
            Your patient account has been created successfully. If email
            verification is enabled in this environment, follow the link in your
            inbox. Otherwise you can sign in immediately.
          </p>

          <div className={styles.confirmationNote}>
            <p>
              Staff accounts are still created by administrators. This public
              registration flow is limited to patients.
            </p>
          </div>

          <AnimatedButton
            variant="primary"
            size="large"
            fullWidth
            onClick={onSignInClick}
          >
            Continue to Sign In
          </AnimatedButton>
        </motion.div>
      </div>
    </div>
  )
}
