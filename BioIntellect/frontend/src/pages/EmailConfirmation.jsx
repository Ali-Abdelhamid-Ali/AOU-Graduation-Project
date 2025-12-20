import { motion } from 'framer-motion'
import { TopBar } from '../components/TopBar'
import { AnimatedButton } from '../components/AnimatedButton'
import { useAuth } from '../context/AuthContext'
import styles from './ResetPassword.module.css' // Reusing compatible styles

/**
 * EmailConfirmation Page
 * 
 * Landing page after user clicks the verification link in their email.
 */

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
                    style={{ textAlign: 'center', padding: '3rem 2rem' }}
                >
                    <div style={{
                        fontSize: '4rem',
                        marginBottom: '1.5rem',
                        background: 'rgba(16, 185, 129, 0.1)',
                        width: '100px',
                        height: '100px',
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto 2rem'
                    }}>
                        📨
                    </div>

                    <h1 className={styles.title}>Email Verified!</h1>
                    <p className={styles.subtitle} style={{ marginBottom: '2rem' }}>
                        Thank you for verifying your email address. Your BioIntellect account is now fully activated and ready for use.
                    </p>

                    <div style={{
                        background: 'var(--color-surface-subtle)',
                        padding: '1.5rem',
                        borderRadius: '12px',
                        marginBottom: '2.5rem',
                        fontSize: '0.9rem',
                        lineHeight: '1.6',
                        color: 'var(--color-text-muted)'
                    }}>
                        <p>You can now sign in to access your secure medical dashboard and manage patient data or clinical records.</p>
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
