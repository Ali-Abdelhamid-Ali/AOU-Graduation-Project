import { brandingConfig } from '../config/brandingConfig'
import ThemeToggle from './ThemeToggle'
import styles from './TopBar.module.css'

/**
 * TopBar Component
 * 
 * Centralized navigation bar with branding, user role status, and global controls.
 */
export const TopBar = ({ userRole = null, onBack = null, onLogout = null }) => {
  return (
    <header className={styles.topbar}>
      <div className={styles.container}>
        {/* Navigation & Brand */}
        <div className={styles.leftSection}>
          {onBack && (
            <button
              className={styles.backButton}
              onClick={onBack}
              title="Return to previous page"
              aria-label="Back"
            >
              <span className={styles.backIcon}>←</span>
              <span className={styles.backText}>Back</span>
            </button>
          )}

          <div className={styles.brand}>
            <button
              className={styles.logo}
              onClick={() => (window.location.href = '/')}
              aria-label="Go to home page"
              type="button"
            >
              <img
                src={brandingConfig.assets.logo}
                alt={`${brandingConfig.brandName} - ${brandingConfig.hospitalName}`}
                className={styles.logoImage}
              />
              <span className={styles.logoText}>{brandingConfig.brandName}</span>
            </button>
          </div>
        </div>

        {/* Global Controls */}
        <div className={styles.controls}>
          {userRole && (
            <div className={styles.userSection}>
              <span className={styles.roleLabel}>
                {userRole === 'administrator' ? '🛡️ Admin' : userRole === 'patient' ? '👤 Patient' : '👨‍⚕️ Medical Staff'}
              </span>
            </div>
          )}

          <div className={styles.divider} />
          <ThemeToggle />

          {onLogout && (
            <button
              className={styles.logoutButton}
              onClick={onLogout}
              aria-label="Sign out"
            >
              Sign Out
            </button>
          )}
        </div>
      </div>
    </header>
  )
}
