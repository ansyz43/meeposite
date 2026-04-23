import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

// Apply persisted theme before first paint.
try {
  const savedTheme = localStorage.getItem('meepo-theme')
  const theme = savedTheme === 'light' || savedTheme === 'dark' ? savedTheme : 'dark'
  document.documentElement.classList.toggle('light', theme === 'light')
  document.documentElement.classList.toggle('dark', theme === 'dark')
} catch {
  // Ignore storage access issues and keep default theme.
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
