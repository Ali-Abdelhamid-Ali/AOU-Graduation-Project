import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '@/store/AuthContext'
import { InputField } from '@/components/ui/InputField'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import { validateStrongPassword } from '@/utils/userFormUtils'
import styles from './PatientSecurity.module.css'

export const PatientSecurity = () => {
    const { updatePassword, signOut } = useAuth()
    const [view, setView] = useState('form') // 'form' | 'success'
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

        if (formData.newPassword !== formData.confirmPassword) {
            setMessage({ type: 'error', text: 'Passwords do not match.' })
            return
        }

        if (formData.currentPassword && formData.newPassword === formData.currentPassword) {
            setMessage({ type: 'error', text: 'New password cannot be the same as your current password. Please choose a different one for better security.' })
            return
        }

        const passwordError = validateStrongPassword(formData.newPassword)
        if (passwordError) {
            setMessage({ type: 'error', text: passwordError })
            return
        }

        setLoading(true)
        try {
            const result = await updatePassword(formData.newPassword, logoutAll)
            if (!result.success) {
                // Check if the backend returned a specific "same password" error
                if (result.error?.toLowerCase().includes('same as old')) {
                    throw new Error('You cannot reuse your current password. Please enter a new one.')
                }
                throw new Error(result.error || 'Failed to update password')
            }

            setView('success')
            setFormData({ currentPassword: '', newPassword: '', confirmPassword: '' })
            setLogoutAll(false)
        } catch (error) {
            setMessage({ type: 'error', text: error.message })
        } finally {
            setLoading(false)
            if (view !== 'success') {
                setTimeout(() => setMessage({ type: '', text: '' }), 5000)
            }
        }
    }

    const handleLogoutOthers = async () => {
        setLoading(true)
        try {
            await signOut('global')
            setMessage({ type: 'success', text: 'Successfully logged out from all other devices.' })
        } catch (error) {
            setMessage({ type: 'error', text: error.message })
        } finally {
            setLoading(false)
            setTimeout(() => setMessage({ type: '', text: '' }), 5000)
        }
    }

    const sessions = [
        { device: 'Current Device (Chrome / Windows)', location: 'Cairo, Egypt', time: 'Active now', isCurrent: true },
        { device: 'Mobile App (iPhone 14)', location: 'Alexandria, Egypt', time: '2 hours ago', isCurrent: false },
    ]

    return (
        <motion.div
            className={styles.container}
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
        >
            <div className={styles.header}>
                <h1 className={styles.title}>Clinical Security Center</h1>
                <p className={styles.subtitle}>Manage your credentials and monitor account access.</p>
            </div>

            <div className={styles.grid}>
                <div className={styles.card}>
                    <h2 className={styles.cardTitle}>🔑 Change Secure Password</h2>

                    {view === 'success' ? (
                        <div className={styles.successState}>
                            <div className={styles.icon}>✓</div>
                            <h3 className={styles.cardTitle}>Password Updated</h3>
                            <p className={styles.description}>
                                Your security credentials have been updated successfully.
                                {logoutAll && " You have also been logged out from all other devices."}
                            </p>
                            <AnimatedButton
                                variant="primary"
                                onClick={() => {
                                    setView('form');
                                    setMessage({ type: '', text: '' });
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
                                onChange={(e) => setFormData({ ...formData, currentPassword: e.target.value })}
                                required
                                placeholder="Enter your current password"
                                helperText="To verify it's really you"
                            />

                            <InputField
                                id="newPassword"
                                label="New Password"
                                type="password"
                                value={formData.newPassword}
                                onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
                                required
                                placeholder="Use 8+ characters"
                                helperText="8+ characters, uppercase, lowercase, number, and symbol"
                            />

                            <InputField
                                id="confirmPassword"
                                label="Confirm New Password"
                                type="password"
                                value={formData.confirmPassword}
                                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
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
                                <label htmlFor="logout_all_form">Logout from other devices</label>
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
                    <h2 className={styles.cardTitle}>🕒 Active Medical Sessions</h2>
                    <p className={styles.cardDesc}>You are currently logged in to these devices.</p>
                    <div className={styles.sessionList}>
                        {sessions.map((session, idx) => (
                            <div key={idx} className={styles.sessionItem}>
                                <div className={styles.sessionIcon}>💻</div>
                                <div className={styles.sessionInfo}>
                                    <div className={styles.device}>
                                        {session.device}
                                        {session.isCurrent && <span className={styles.currentBadge}>Current</span>}
                                    </div>
                                    <div className={styles.meta}>{session.location} • {session.time}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                    <button
                        className={styles.logoutAll}
                        onClick={handleLogoutOthers}
                        disabled={loading}
                    >
                        Log Out From All Other Devices
                    </button>
                    {message.type === 'success' && view !== 'success' && (
                        <div className={`${styles.message} ${styles.success}`} style={{ marginTop: '1rem' }}>
                            {message.text}
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    )
}
