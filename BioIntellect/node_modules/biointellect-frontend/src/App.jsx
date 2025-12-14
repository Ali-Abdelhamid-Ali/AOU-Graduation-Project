import { useState } from 'react'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from './context/ToastContext'
import { SelectRole } from './pages/SelectRole'
import { Login } from './pages/Login'
import { SignUp } from './pages/SignUp'
import { ResetPassword } from './pages/ResetPassword'
import './index.css'

/**
 * BioIntellect - Medical Intelligence Platform
 * 
 * Frontend Application
 * 
 * Flow:
 * 1. SelectRole - User chooses Doctor or Patient
 * 2. Login - User logs in with email and password
 * 3. SignUp - User creates new account
 * 4. ResetPassword - User resets forgotten password
 * 
 * Stack:
 * - React 18 with Hooks (Functional Components)
 * - Context API for state management
 * - Framer Motion for animations
 * - CSS Modules for styling
 * 
 * Design:
 * - Medical-grade UI
 * - Healthcare SaaS inspired
 * - Eye-friendly colors
 * - Accessible (WCAG 2.1)
 * - RTL ready
 * 
 * Ready for:
 * - Supabase Auth integration
 * - Supabase Database integration
 * - Future Dashboard pages
 * - RBAC implementation
 */

function App() {
  // Current page state
  const [currentPage, setCurrentPage] = useState('selectRole')

  const handleRoleSelected = (role) => {
    setCurrentPage('login')
  }

  const handleLoginSuccess = () => {
    // Future: Navigate to dashboard
    alert(
      '✓ Signed in successfully!\n\nThis app is ready to be connected to Supabase.\nComing soon: Dashboard and more features'
    )
    // Reset to role selection for demo
    setCurrentPage('selectRole')
  }

  const handleSignUpSuccess = () => {
    alert(
      '✓ Account created successfully!\n\nThis account will be connected to Supabase for email verification'
    )
    setCurrentPage('login')
  }

  const handleResetPassword = () => {
    setCurrentPage('resetPassword')
  }

  const handleResetSuccess = () => {
    setCurrentPage('login')
  }

  const handleBackToLogin = () => {
    setCurrentPage('login')
  }

  return (
    <ToastProvider>
      <AuthProvider>
        <div className="app">
          {currentPage === 'selectRole' && (
            <SelectRole onRoleSelected={handleRoleSelected} />
          )}

          {currentPage === 'login' && (
            <Login
              onLoginSuccess={handleLoginSuccess}
              onSignUpClick={() => setCurrentPage('signUp')}
              onForgotPasswordClick={handleResetPassword}
            />
          )}

          {currentPage === 'signUp' && (
            <SignUp
              onSignUpSuccess={handleSignUpSuccess}
              onLoginClick={() => setCurrentPage('login')}
            />
          )}

          {currentPage === 'resetPassword' && (
            <ResetPassword
              onResetSuccess={handleResetSuccess}
              onBackToLogin={handleBackToLogin}
            />
          )}
        </div>
      </AuthProvider>
    </ToastProvider>
  )
}

export default App
