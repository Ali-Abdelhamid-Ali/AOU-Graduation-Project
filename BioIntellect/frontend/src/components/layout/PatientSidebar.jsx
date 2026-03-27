import { motion } from 'framer-motion'
import { Link, useLocation } from 'react-router-dom'

import { useAuth } from '@/store/AuthContext'
import styles from './PatientSidebar.module.css'

const menuItems = [
  { path: '/patient-dashboard', label: 'Dashboard', glyph: 'DB' },
  { path: '/patient-results', label: 'Medical Results', glyph: 'RS' },
  { path: '/patient-appointments', label: 'Appointments', glyph: 'AP' },
  { path: '/patient-profile', label: 'Personal Profile', glyph: 'PF' },
  { path: '/patient-security', label: 'Security Settings', glyph: 'SC' },
]

export const PatientSidebar = ({ isCollapsed, setIsCollapsed }) => {
  const { currentUser, signOut } = useAuth()
  const location = useLocation()

  const displayName =
    currentUser?.full_name ||
    [currentUser?.first_name, currentUser?.last_name].filter(Boolean).join(' ') ||
    'Patient Portal'

  const profileInitials =
    displayName
      .split(' ')
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0])
      .join('')
      .toUpperCase() || 'PT'

  return (
    <motion.aside
      className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ''}`}
      initial={false}
      animate={{ inlineSize: isCollapsed ? '88px' : '292px' }}
    >
      <div className={styles.topSection}>
        <div className={styles.logoContainer}>
          <div className={styles.logoIcon}>BI</div>
          {!isCollapsed && (
            <div>
              <strong className={styles.logoText}>BioIntellect</strong>
              <span className={styles.logoMeta}>Patient Portal</span>
            </div>
          )}
        </div>
        <button
          type="button"
          className={styles.collapseToggle}
          onClick={() => setIsCollapsed(!isCollapsed)}
          aria-label={isCollapsed ? 'Expand patient navigation' : 'Collapse patient navigation'}
        >
          {isCollapsed ? '+' : '-'}
        </button>
      </div>

      <div className={styles.profileSection}>
        <div className={styles.avatarWrapper}>
          {currentUser?.photo_url ? (
            <img src={currentUser.photo_url} alt={displayName} className={styles.avatar} />
          ) : (
            <div className={styles.avatarFallback}>{profileInitials}</div>
          )}
          <div className={styles.statusDot} />
        </div>
        {!isCollapsed && (
          <div className={styles.profileInfo}>
            <h3 className={styles.userName}>{displayName}</h3>
            <span className={styles.userStatus}>{currentUser?.mrn || 'Verified patient access'}</span>
          </div>
        )}
      </div>

      <nav className={styles.nav} aria-label="Patient portal navigation">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`${styles.navLink} ${location.pathname === item.path ? styles.active : ''}`}
          >
            <span className={styles.navIcon}>{item.glyph}</span>
            {!isCollapsed && <span className={styles.navLabel}>{item.label}</span>}
          </Link>
        ))}
      </nav>

      <div className={styles.footer}>
        <button type="button" className={styles.logoutBtn} onClick={() => signOut()}>
          <span className={styles.navIcon}>LO</span>
          {!isCollapsed && <span>Log out</span>}
        </button>
      </div>
    </motion.aside>
  )
}
