"use client"

import { useContext, useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import AuthContext from '@/store/AuthContext'
import { getThemeStorageKey, readThemePreference, writeThemePreference } from '@/utils/themeMode'

export default function ThemeToggle() {
  const authContext = useContext(AuthContext)
  const currentUser = authContext?.currentUser || null
  const userRole = authContext?.userRole || null
  const storageKey = useMemo(() => getThemeStorageKey(currentUser, userRole), [
    currentUser?.auth_user_id,
    currentUser?.user_id,
    currentUser?.profile_id,
    currentUser?.id,
    currentUser?.user_role,
    currentUser?.role,
    userRole,
  ])

  const [isDark, setIsDark] = useState(() => readThemePreference(storageKey))

  useEffect(() => {
    setIsDark(readThemePreference(storageKey))
  }, [storageKey])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
    writeThemePreference(storageKey, isDark)
  }, [isDark, storageKey])

  const toggle = () => setIsDark(prev => !prev)

  return (
    <motion.button
      type="button"
      onClick={toggle}
      style={{
        inlineSize: 100,
        blockSize: 50,
        backgroundColor: 'var(--color-toggle-bg)',
        borderRadius: 50,
        cursor: 'pointer',
        border: 'none',
        display: 'flex',
        padding: 5,
        alignItems: 'center',
        boxSizing: 'border-box',
        position: 'relative',
        boxShadow: 'var(--color-toggle-track-shadow)',
      }}
      animate={{
        backgroundColor: isDark ? 'var(--color-gray-300)' : 'var(--color-toggle-bg)',
        boxShadow: isDark
          ? 'var(--color-toggle-track-shadow-dark)'
          : 'var(--color-toggle-track-shadow)',
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      className="theme-toggle-button"
    >
      {/* Emoji - يتغير حسب المود */}
      <motion.span
        style={{
          fontSize: 22,
          position: 'absolute',
          insetInlineStart: isDark ? 'auto' : '8px',
          insetInlineEnd: isDark ? '8px' : 'auto',
          display: 'flex',
          alignItems: 'center',
        }}
        initial={false}
        animate={{
          opacity: 1,
        }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      >
        {isDark ? '🌙' : '☀️'}
      </motion.span>

      {/* Handle/Dot - عكس اتجاه الايموجي */}
      <motion.div
        style={{
          inlineSize: 38,
          blockSize: 38,
          backgroundColor: isDark ? 'var(--color-primary)' : 'var(--color-toggle-handle-light)',
          borderRadius: '50%',
          boxShadow: isDark
            ? '0 2px 8px rgba(59, 130, 246, 0.4)'
            : '0 2px 8px rgba(251, 191, 36, 0.4)',
          position: 'absolute',
          insetInlineStart: isDark ? '8px' : 'auto',
          insetInlineEnd: isDark ? 'auto' : '8px',
        }}
        animate={{
          insetInlineStart: isDark ? '8px' : 'auto',
          insetInlineEnd: isDark ? 'auto' : '8px',
          backgroundColor: isDark ? 'var(--color-primary)' : 'var(--color-toggle-handle-light)',
          boxShadow: isDark
            ? '0 2px 8px rgba(59, 130, 246, 0.4)'
            : '0 2px 8px rgba(251, 191, 36, 0.4)',
        }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      />
    </motion.button>
  )
}
