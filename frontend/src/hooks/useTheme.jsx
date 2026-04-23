import { useCallback, useEffect, useState } from 'react'

const THEME_KEY = 'meepo-theme'
const THEME_EVENT = 'meepo-theme-change'

function getInitialTheme() {
  try {
    const saved = localStorage.getItem(THEME_KEY)
    if (saved === 'light' || saved === 'dark') return saved
  } catch {
    // ignore
  }
  return 'dark'
}

function applyTheme(theme) {
  document.documentElement.classList.toggle('light', theme === 'light')
  document.documentElement.classList.toggle('dark', theme === 'dark')
}

function writeTheme(theme) {
  try {
    localStorage.setItem(THEME_KEY, theme)
  } catch {
    // ignore
  }
  applyTheme(theme)
  try {
    window.dispatchEvent(new CustomEvent(THEME_EVENT, { detail: theme }))
  } catch {
    // ignore
  }
}

export function useTheme() {
  const [theme, setThemeState] = useState(getInitialTheme)

  // Sync across all useTheme consumers in the app via a window event.
  useEffect(() => {
    function onThemeChange(e) {
      const next = e?.detail
      if (next === 'light' || next === 'dark') setThemeState(next)
    }
    function onStorage(e) {
      if (e.key === THEME_KEY && (e.newValue === 'light' || e.newValue === 'dark')) {
        setThemeState(e.newValue)
      }
    }
    window.addEventListener(THEME_EVENT, onThemeChange)
    window.addEventListener('storage', onStorage)
    return () => {
      window.removeEventListener(THEME_EVENT, onThemeChange)
      window.removeEventListener('storage', onStorage)
    }
  }, [])

  const setTheme = useCallback((nextTheme) => {
    const value = nextTheme === 'light' ? 'light' : 'dark'
    setThemeState(value)
    writeTheme(value)
  }, [])

  const toggleTheme = useCallback(() => {
    setThemeState((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark'
      writeTheme(next)
      return next
    })
  }, [])

  return {
    theme,
    isLight: theme === 'light',
    isDark: theme === 'dark',
    setTheme,
    toggleTheme,
  }
}
