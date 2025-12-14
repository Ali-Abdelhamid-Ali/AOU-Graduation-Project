import { useState, useEffect } from 'react'
import styles from './TopBar.module.css'
import ThemeToggle from './ThemeToggle'

/**
 * TopBar Component
 * 
 * Fixed navigation bar at the top of the application
 * Features:
 * - BioIntellect branding
 * - User role display
 * - Professional healthcare design
 * - Responsive layout
 */

export const TopBar = ({ userRole = null }) => {
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    // initialize theme from localStorage or OS preference
    const stored = localStorage.getItem('biointellect_theme')
    if (stored) {
      setIsDark(stored === 'dark')
      document.documentElement.classList.toggle('dark', stored === 'dark')
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setIsDark(true)
      document.documentElement.classList.add('dark')
    }
  }, [])


  const [layoutMode, setLayoutMode] = useState(() => localStorage.getItem('layout_mode') === 'true')

  const toggleLayoutMode = () => {
    const next = !layoutMode
    setLayoutMode(next)
    localStorage.setItem('layout_mode', next ? 'true' : 'false')
    window.dispatchEvent(new CustomEvent('layout_mode_change', { detail: { enabled: next } }))
  }

  return (
    <header className={styles.topbar}>
      <div className={styles.container}>
        {/* Logo / Brand */}
        <div className={styles.brand}>
          <button
            className={styles.logo}
            onClick={() => (window.location.href = '/')}
            aria-label="Go to home page"
            type="button"
          >
            <img
              src="/src/images/BioIntellect.png"
              alt="BioIntellect Logo"
              className={styles.logoImage}
            />
            <span className={styles.logoText}>BioIntellect</span>
          </button>
        </div>


        {/* Center Spacer */}
        <div className={styles.spacer}>
          {/* User Info */}
          {userRole && (
            <div className={styles.userSection}>
              <span className={styles.roleLabel}>
                {userRole === 'doctor' ? '👨‍⚕️ Doctor' : '👤 Patient'}
              </span>
            </div>
          )}
        </div>

        {/* Right Controls */}
        <div className={styles.controls}>
            <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
