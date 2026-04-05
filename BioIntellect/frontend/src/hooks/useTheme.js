import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '@/store/AuthContext'
import { getThemeStorageKey, readThemePreference, writeThemePreference } from '@/utils/themeMode'

export const useTheme = () => {
  const { currentUser, userRole } = useAuth()
  const storageKey = useMemo(() => getThemeStorageKey(currentUser, userRole), [currentUser, userRole])

  const [isDark, setIsDark] = useState(() => readThemePreference(storageKey))

  useEffect(() => {
    setIsDark(readThemePreference(storageKey))
  }, [storageKey])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
    writeThemePreference(storageKey, isDark)
  }, [isDark, storageKey])

  const toggle = () => setIsDark((prev) => !prev)

  return { isDark, toggle }
}
