import { useState } from 'react'
import { motion } from 'framer-motion'

import { useAuth } from '@/store/AuthContext'
import { TopBar } from '@/components/layout/TopBar'
import styles from './SelectRole.module.css'

import securityIcon from '@/assets/images/icons/security.png'
import insightsIcon from '@/assets/images/icons/insights.png'
import analyticsIcon from '@/assets/images/icons/analytics.png'

export const SelectRole = ({ onRoleSelected, onBack }) => {
  const { selectRole } = useAuth()
  const [selectedRole, setSelectedRole] = useState(null)

  const handleRoleSelect = (role) => {
    setSelectedRole(role)
    selectRole(role)

    setTimeout(() => {
      onRoleSelected(role)
    }, 300)
  }

  const roleOptions = [
    {
      id: 'doctor',
      label: 'Doctor',
      icon: securityIcon,
      description: 'Sign in to access clinical AI modules',
      color: 'primary',
    },
    {
      id: 'patient',
      label: 'Patient',
      icon: insightsIcon,
      description: 'Sign in or create an account to access your records',
      color: 'secondary',
    },
    {
      id: 'admin',
      label: 'Administrator',
      icon: analyticsIcon,
      description: 'System governance and staff management',
      color: 'accent',
    },
  ]

  return (
    <div className={styles.pageWrapper}>
      <TopBar onBack={onBack} />

      <div className={styles.container}>
        <motion.div
          className={styles.content}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className={styles.header}>
            <h1 className={styles.title}>
              Welcome to <span className={styles.highlight}>BioIntellect</span>
            </h1>
            <p className={styles.subtitle}>
              A clinical-grade platform to improve healthcare outcomes
            </p>
          </div>

          <div className={styles.rolesGrid}>
            {roleOptions.map((role, index) => (
              <motion.div
                key={role.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
              >
                <button
                  className={`${styles.roleCard} ${
                    selectedRole === role.id ? styles.selected : ''
                  } ${styles[role.color]}`}
                  onClick={() => handleRoleSelect(role.id)}
                >
                  <div className={styles.iconContainer}>
                    <img src={role.icon} alt={role.label} className={styles.roleIconImg} />
                  </div>
                  <h2 className={styles.roleLabel}>{role.label}</h2>
                  <p className={styles.roleDescription}>{role.description}</p>
                  <div className={styles.arrow}>{'->'}</div>
                </button>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
