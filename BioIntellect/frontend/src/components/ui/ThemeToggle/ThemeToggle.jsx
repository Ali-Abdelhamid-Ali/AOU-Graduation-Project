"use client"

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window === 'undefined') return false
    const stored = localStorage.getItem('biointellect_theme')
    return stored === 'dark'
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
    localStorage.setItem('biointellect_theme', isDark ? 'dark' : 'light')
  }, [isDark])

  const toggle = () => setIsDark(prev => !prev)

  return (
    <motion.button
      type="button"
      onClick={toggle}
      style={{
        inlineSize: 100,
        blockSize: 50,
        backgroundColor: 'var(--color-gray-200)',
        borderRadius: 50,
        cursor: 'pointer',
        border: 'none',
        display: 'flex',
        padding: 5,
        alignItems: 'center',
        boxSizing: 'border-box',
        position: 'relative',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
      }}
      animate={{
        backgroundColor: isDark ? 'var(--color-gray-300)' : 'var(--color-gray-200)',
        boxShadow: isDark ? '0 2px 8px rgba(0, 0, 0, 0.3)' : '0 2px 8px rgba(0, 0, 0, 0.1)',
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
          backgroundColor: isDark ? 'var(--color-primary)' : '#fbbf24',
          borderRadius: '50%',
          boxShadow: isDark ? '0 2px 8px rgba(77, 148, 255, 0.4)' : '0 2px 8px rgba(251, 191, 36, 0.4)',
          position: 'absolute',
          insetInlineStart: isDark ? '8px' : 'auto',
          insetInlineEnd: isDark ? 'auto' : '8px',
        }}
        animate={{
          insetInlineStart: isDark ? '8px' : 'auto',
          insetInlineEnd: isDark ? 'auto' : '8px',
          backgroundColor: isDark ? 'var(--color-primary)' : '#fbbf24',
          boxShadow: isDark ? '0 2px 8px rgba(77, 148, 255, 0.4)' : '0 2px 8px rgba(251, 191, 36, 0.4)',
        }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      />
    </motion.button>
  )
}
