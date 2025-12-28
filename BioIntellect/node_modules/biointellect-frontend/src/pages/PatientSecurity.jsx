import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { supabase } from '../config/supabase'
import { InputField } from '../components/InputField'
import { AnimatedButton } from '../components/AnimatedButton'
import styles from './PatientSecurity.module.css'

export const PatientSecurity = () => {
    const { currentUser } = useAuth()
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState({ type: '', text: '' })
    const [formData, setFormData] = useState({
        newPassword: '',
        confirmPassword: '',
    })

    const handlePasswordChange = async (e) => {
        e.preventDefault()
        if (formData.newPassword !== formData.confirmPassword) {
            setMessage({ type: 'error', text: 'Passwords do not match.' })
            return
        }

        setLoading(true)
        try {
            const { error } = await supabase.auth.updateUser({
                password: formData.newPassword
            })

            if (error) throw error

            setMessage({ type: 'success', text: 'Password updated successfully!' })
            setFormData({ newPassword: '', confirmPassword: '' })
        } catch (error) {
            setMessage({ type: 'error', text: error.message })
        } finally {
            setLoading(false)
            setTimeout(() => setMessage({ type: '', text: '' }), 3000)
        }
    }

    const handleLogoutOthers = async () => {
        setLoading(true)
        try {
            const { error } = await supabase.auth.signOut({ scope: 'others' })
            if (error) throw error
            setMessage({ type: 'success', text: 'Successfully logged out from all other devices.' })
        } catch (error) {
            setMessage({ type: 'error', text: error.message })
        } finally {
            setLoading(false)
            setTimeout(() => setMessage({ type: '', text: '' }), 3000)
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
                    <form onSubmit={handlePasswordChange} className={styles.form}>
                        <InputField
                            id="newPassword"
                            label="New Password"
                            type="password"
                            value={formData.newPassword}
                            onChange={(e) => setFormData({ ...formData, newPassword: e.target.value })}
                            required
                            placeholder="Min 8 characters"
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

                        <AnimatedButton
                            type="submit"
                            variant="primary"
                            isLoading={loading}
                            fullWidth
                        >
                            Update Security Credentials
                        </AnimatedButton>
                    </form>
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
                </div>
            </div>
        </motion.div>
    )
}
