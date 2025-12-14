import { useState } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { TopBar } from '../components/TopBar'
import styles from './SelectRole.module.css'

/**
 * SelectRole Page
 * 
 * First step in user onboarding
 * Users select their role (Doctor or Patient)
 * 
 * Features:
 * - Clean role selection interface
 * - Medical-grade design
 * - Smooth animations
 * - Context-based state management
 */

export const SelectRole = ({ onRoleSelected }) => {
  const { selectRole } = useAuth()
  const [selectedRole, setSelectedRole] = useState(null)

  const handleRoleSelect = (role) => {
    setSelectedRole(role)
    selectRole(role)
    // Trigger transition to next page
    setTimeout(() => {
      onRoleSelected(role)
    }, 300)
  }

  const roleOptions = [
    {
      id: 'doctor',
      label: 'Doctor',
      icon: '👨‍⚕️',
      description: 'Sign in as a doctor',
      color: 'primary',
    },
    {
      id: 'patient',
      label: 'Patient',
      icon: '👤',
      description: 'Sign in as a patient',
      color: 'secondary',
    },
  ]

  return (
    <div className={styles.pageWrapper}>
      <TopBar />

      <div className={styles.container}>
        <motion.div
          className={styles.content}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* Header */}
          <div className={styles.header}>
            <h1 className={styles.title}>
              Welcome to <span className={styles.highlight}>BioIntellect</span>
            </h1>
            <p className={styles.subtitle}>
              A clinical-grade platform to improve healthcare outcomes
            </p>
          </div>

          {/* Role Selection Cards */}
          <div className={styles.rolesGrid}>
            {roleOptions.map((role, index) => (
              <motion.div
                key={role.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
              >
                <button
                  className={`${styles.roleCard} ${selectedRole === role.id ? styles.selected : ''
                    } ${styles[role.color]}`}
                  onClick={() => handleRoleSelect(role.id)}
                >
                  <div className={styles.icon}>{role.icon}</div>
                  <h2 className={styles.roleLabel}>{role.label}</h2>
                  <p className={styles.roleDescription}>{role.description}</p>
                  <div className={styles.arrow}>→</div>
                </button>
              </motion.div>
            ))}
          </div>

          {/* Info Box */}

        </motion.div>
      </div>
    </div>
  )
}
