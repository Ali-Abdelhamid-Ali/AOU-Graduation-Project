import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './PatientSidebar.module.css'

// Professional medical icons could be SVG or images
// I'll use placeholders for icons that can be replaced or matched with existing ones

export const PatientSidebar = ({ isCollapsed, setIsCollapsed }) => {
    const { currentUser, signOut } = useAuth()
    const location = useLocation()

    const menuItems = [
        { path: '/patient-dashboard', label: 'Dashboard', icon: '📊' },
        { path: '/patient-results', label: 'Medical Results', icon: '🧬' },
        { path: '/patient-appointments', label: 'Appointments', icon: '📅' },
        { path: '/patient-profile', label: 'Personal Profile', icon: '👤' },
        { path: '/patient-security', label: 'Security Settings', icon: '🛡️' },
    ]

    return (
        <motion.aside
            className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ''}`}
            initial={false}
            animate={{ width: isCollapsed ? '80px' : '280px' }}
        >
            <div className={styles.topSection}>
                <div className={styles.logoContainer}>
                    <div className={styles.logoIcon}>B</div>
                    {!isCollapsed && <span className={styles.logoText}>BioIntellect</span>}
                </div>
                <button
                    className={styles.collapseToggle}
                    onClick={() => setIsCollapsed(!isCollapsed)}
                >
                    {isCollapsed ? '→' : '←'}
                </button>
            </div>

            <div className={styles.profileSection}>
                <div className={styles.avatarWrapper}>
                    <img
                        src={currentUser?.photo_url || 'https://via.placeholder.com/150'}
                        alt="User"
                        className={styles.avatar}
                    />
                    <div className={styles.statusDot} />
                </div>
                {!isCollapsed && (
                    <motion.div
                        className={styles.profileInfo}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                    >
                        <h3 className={styles.userName}>{currentUser?.full_name}</h3>
                        <span className={styles.userStatus}>Verified Patient</span>
                    </motion.div>
                )}
            </div>

            <nav className={styles.nav}>
                {menuItems.map((item) => (
                    <Link
                        key={item.path}
                        to={item.path}
                        className={`${styles.navLink} ${location.pathname === item.path ? styles.active : ''}`}
                    >
                        <span className={styles.navIcon}>{item.icon}</span>
                        {!isCollapsed && (
                            <motion.span
                                className={styles.navLabel}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                            >
                                {item.label}
                            </motion.span>
                        )}
                    </Link>
                ))}
            </nav>

            <div className={styles.footer}>
                <button className={styles.logoutBtn} onClick={signOut}>
                    <span className={styles.navIcon}>🚪</span>
                    {!isCollapsed && <span>Logout</span>}
                </button>
            </div>
        </motion.aside>
    )
}
