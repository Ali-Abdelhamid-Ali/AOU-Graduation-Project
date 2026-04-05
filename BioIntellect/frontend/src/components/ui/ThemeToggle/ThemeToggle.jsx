"use client"

import { motion } from 'framer-motion'
import { useTheme } from '@/hooks/useTheme'

export default function ThemeToggle() {
  const { isDark, toggle } = useTheme()

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
