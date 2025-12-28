import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { TopBar } from '../components/TopBar'
import { InputField } from '../components/InputField'
import { AnimatedButton } from '../components/AnimatedButton'
import styles from './ForcePasswordReset.module.css'

export const ForcePasswordReset = () => {
    const { completeForcedReset, signOut } = useAuth()
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

        if (formData.newPassword.length < 8) {
            setError('Password must be at least 8 characters long.')
            return
        }

        if (formData.newPassword !== formData.confirmPassword) {
            setError('Passwords do not match.')
            return
        }

        setLoading(true)
        const result = await completeForcedReset(formData.newPassword)
        if (result.success) {
            setSuccess(true)
        } else {
            setError(result.error)
            setLoading(false)
        }
    }

    if (success) {
        return (
            <div className={styles.container}>
                <div className={styles.successCard}>
                    <div className={styles.successIcon}>✓</div>
                    <h2>Security Update Successful</h2>
                    <p>Your password has been updated. You can now access your clinical dashboard safely.</p>
                    <AnimatedButton
                        variant="primary"
                        onClick={() => window.location.reload()}
                    >
                        Enter Portal
                    </AnimatedButton>
                </div>
            </div>
        )
    }

    return (
        <div className={styles.pageWrapper}>
            <div className={styles.content}>
                <motion.div
                    className={styles.resetCard}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                >
                    <div className={styles.header}>
                        <div className={styles.badge}>SECURITY ALERT</div>
                        <h1 className={styles.title}>Mandatory Security Update</h1>
                        <p className={styles.subtitle}>
                            To ensure the highest level of protection for your medical records,
                            please establish a new secure password before proceeding.
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className={styles.form}>
                        <InputField
                            id="new-password"
                            label="New Secure Password"
                            type="password"
                            value={formData.newPassword}
                            onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
                            required
                            placeholder="At least 8 characters"
                        />
                        <InputField
                            id="confirm-password"
                            label="Confirm New Password"
                            type="password"
                            value={formData.confirmPassword}
                            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                            required
                        />

                        {error && (
                            <motion.div
                                className={styles.error}
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                            >
                                {error}
                            </motion.div>
                        )}

                        <div className={styles.actions}>
                            <AnimatedButton
                                type="submit"
                                variant="primary"
                                fullWidth
                                isLoading={loading}
                            >
                                Update & Continue
                            </AnimatedButton>

                            <button
                                type="button"
                                className={styles.logoutButton}
                                onClick={signOut}
                            >
                                Logout
                            </button>
                        </div>
                    </form>

                    <div className={styles.securityInfo}>
                        <p>💡 Tips for a strong password:</p>
                        <ul>
                            <li>Use 8+ characters</li>
                            <li>Mix uppercase & lowercase</li>
                            <li>Include numbers & symbols</li>
                        </ul>
                    </div>
                </motion.div>
            </div>
        </div>
    )
}
