import { useState } from 'react'
import { motion } from 'framer-motion'

import { useAuth } from '@/store/AuthContext'
import { InputField } from '@/components/ui/InputField'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import { validateStrongPassword } from '@/utils/userFormUtils'
import styles from './PatientSecurity.module.css'

export const PatientSecurity = () => {
  const { updatePassword, signOut } = useAuth()
  const [view, setView] = useState('form')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [logoutAll, setLogoutAll] = useState(false)
  const [formData, setFormData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  })

  const handlePasswordChange = async (e) => {
    e.preventDefault()

    if (!formData.currentPassword) {
      setMessage({ type: 'error', text: 'Current password is required.' })
      return
    }

    if (formData.newPassword !== formData.confirmPassword) {
      setMessage({ type: 'error', text: 'Passwords do not match.' })
      return
    }

    const passwordError = validateStrongPassword(formData.newPassword)
    if (passwordError) {
      setMessage({ type: 'error', text: passwordError })
      return
    }

    setLoading(true)
    try {
      const result = await updatePassword(
        formData.newPassword,
        logoutAll,
        formData.currentPassword
      )
      if (!result.success) {
        throw new Error(result.error || 'Failed to update password')
      }

      setView('success')
      setFormData({ currentPassword: '', newPassword: '', confirmPassword: '' })
      setLogoutAll(false)
      setMessage({ type: '', text: '' })
    } catch (error) {
      setMessage({ type: 'error', text: error.message })
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      className={styles.container}
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
    >
      <div className={styles.header}>
        <h1 className={styles.title}>Clinical Security Center</h1>
        <p className={styles.subtitle}>
          Manage your password and revoke active sessions securely.
        </p>
      </div>

      <div className={styles.grid}>
        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Password Management</h2>

          {view === 'success' ? (
            <div className={styles.successState}>
              <div className={styles.icon}>OK</div>
              <h3 className={styles.cardTitle}>Password Updated</h3>
              <p className={styles.description}>
                Your password has been updated successfully.
                {logoutAll ? ' Other sessions were revoked during the update.' : ''}
              </p>
              <AnimatedButton
                variant="primary"
                onClick={() => {
                  setView('form')
                  setMessage({ type: '', text: '' })
                }}
              >
                Back to Security Settings
              </AnimatedButton>
            </div>
          ) : (
            <form onSubmit={handlePasswordChange} className={styles.form}>
              <InputField
                id="currentPassword"
                label="Current Password"
                type="password"
                value={formData.currentPassword}
                onChange={(e) =>
                  setFormData({ ...formData, currentPassword: e.target.value })
                }
                required
                autoComplete="current-password"
              />

              <InputField
                id="newPassword"
                label="New Password"
                type="password"
                value={formData.newPassword}
                onChange={(e) =>
                  setFormData({ ...formData, newPassword: e.target.value })
                }
                required
                placeholder="Use 8+ characters"
                helperText="Use a strong, unique password that is not shared with any other system."
              />

              <InputField
                id="confirmPassword"
                label="Confirm New Password"
                type="password"
                value={formData.confirmPassword}
                onChange={(e) =>
                  setFormData({ ...formData, confirmPassword: e.target.value })
                }
                required
              />

              {message.text && (
                <div className={`${styles.message} ${styles[message.type]}`}>
                  {message.text}
                </div>
              )}

              <div className={styles.checkboxGroup}>
                <input
                  type="checkbox"
                  id="logout_all_form"
                  checked={logoutAll}
                  onChange={(e) => setLogoutAll(e.target.checked)}
                />
                <label htmlFor="logout_all_form">
                  Revoke other sessions after updating the password
                </label>
              </div>

              <AnimatedButton
                type="submit"
                variant="primary"
                isLoading={loading}
                fullWidth
              >
                Update Security Credentials
              </AnimatedButton>
            </form>
          )}
        </div>

        <div className={styles.card}>
          <h2 className={styles.cardTitle}>Session Controls</h2>
          <p className={styles.cardDesc}>
            Session management coming soon. To secure your account today, use the
            action below to sign out of all devices at once.
          </p>

          <div className={styles.noticeBox}>
            <p className={styles.noticeTitle}>No live device list is available yet.</p>
            <p className={styles.noticeBody}>
              The backend does not currently expose per-device session tracking,
              so this page only offers password updates and full-session revocation.
            </p>
          </div>

          <button
            className={styles.logoutAll}
            onClick={() => signOut('global')}
            disabled={loading}
          >
            Sign Out of All Devices
          </button>
        </div>
      </div>
    </motion.div>
  )
}
