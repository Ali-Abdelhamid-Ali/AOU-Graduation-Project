import { useState, useEffect, useMemo } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import ErrorBoundary from './components/ErrorBoundary'

// Page Imports
import { SelectRole } from './pages/SelectRole'
import { Login } from './pages/Login'
import { SignUp } from './pages/SignUp'
import { ResetPassword } from './pages/ResetPassword'
import { EmailConfirmation } from './pages/EmailConfirmation'
import { HomePage } from './pages/HomePage'
import { AdminDashboard } from './pages/AdminDashboard'
import { PatientDashboard } from './pages/PatientDashboard'
import { CreatePatient } from './pages/CreatePatient'
import { CreateDoctor } from './pages/CreateDoctor'
import { ProjectAbout } from './pages/ProjectAbout'
import { EcgAnalysis } from './pages/EcgAnalysis'
import { MriSegmentation } from './pages/MriSegmentation'
import { MedicalLlm } from './pages/MedicalLlm'
import './index.css'

function AppContent() {
  const { isAuthenticated, userRole, signOut } = useAuth()
  const [currentPage, setCurrentPage] = useState('home')
  const [history, setHistory] = useState(['home'])

  const navigateTo = (page, options = {}) => {
    if (options.clear) {
      setHistory([page])
    } else if (options.replace) {
      setHistory(prev => [...prev.slice(0, -1), page])
    } else {
      setHistory(prev => [...prev, page])
    }
    setCurrentPage(page)
  }

  const handleBack = () => {
    if (history.length > 1) {
      const newHistory = [...history]
      newHistory.pop()
      const prevPage = newHistory[newHistory.length - 1]
      setHistory(newHistory)
      setCurrentPage(prevPage)
    }
  }

  const handleLogout = async () => {
    await signOut()
    navigateTo('home', { clear: true })
  }

  // Effect handles redirection logic based on authentication state and URL hashes
  useEffect(() => {
    const hash = window.location.hash
    const isRecovery = hash && hash.includes('type=recovery')
    const isSignup = hash && hash.includes('type=signup')

    if (isRecovery) {
      navigateTo('resetPassword', { replace: true })
      return
    }
    if (isSignup) {
      navigateTo('emailConfirmation', { replace: true })
      return
    }

    if (isAuthenticated) {
      if (userRole === 'patient') {
        if (!['patientDashboard'].includes(currentPage)) {
          navigateTo('patientDashboard', { clear: true })
        }
      } else if (userRole) {
        // Staff/Admin roles go to unified AdminDashboard unless already on a specific sub-page
        const staffPages = ['adminDashboard', 'createPatient', 'createDoctor', 'ecgAnalysis', 'mriSegmentation', 'medicalLlm']
        if (!staffPages.includes(currentPage)) {
          navigateTo('adminDashboard', { clear: true })
        }
      }
    } else {
      const publicPages = ['home', 'login', 'signUp', 'resetPassword', 'selectRole', 'emailConfirmation', 'projectAbout']
      if (!publicPages.includes(currentPage)) {
        navigateTo('home', { clear: true })
      }
    }
  }, [isAuthenticated, userRole])

  /**
   * Page Registry
   * Organized mapping of page keys to component instances for cleaner rendering logic.
   */
  const renderPage = () => {
    switch (currentPage) {
      // Public Pages
      case 'home': return <HomePage onEnter={() => navigateTo('selectRole')} onAboutClick={() => navigateTo('projectAbout')} />
      case 'selectRole': return <SelectRole onRoleSelected={() => navigateTo('login')} onBack={handleBack} />
      case 'login': return (
        <Login
          onLoginSuccess={(role) => navigateTo(role === 'patient' ? 'patientDashboard' : 'adminDashboard', { clear: true })}
          onSignUpClick={() => navigateTo('signUp')}
          onForgotPasswordClick={() => navigateTo('resetPassword')}
          onBack={handleBack}
        />
      )
      case 'signUp': return (
        <SignUp
          onSignUpSuccess={() => navigateTo('login', { replace: true })}
          onLoginClick={() => navigateTo('login', { replace: true })}
          onBack={handleBack}
        />
      )
      case 'resetPassword': return (
        <ResetPassword
          onResetSuccess={() => navigateTo('login', { clear: true })}
          onBackToLogin={() => navigateTo('login', { replace: true })}
          onBack={handleBack}
        />
      )
      case 'emailConfirmation': return <EmailConfirmation onSignInClick={() => navigateTo('selectRole', { clear: true })} />
      case 'projectAbout': return <ProjectAbout onBack={handleBack} />

      // Protected Dashboards
      case 'adminDashboard': return (
        <AdminDashboard
          userRole={userRole}
          onLogout={handleLogout}
          onCreatePatient={() => navigateTo('createPatient')}
          onCreateDoctor={() => navigateTo('createDoctor')}
          onEcgAnalysis={() => navigateTo('ecgAnalysis')}
          onMriSegmentation={() => navigateTo('mriSegmentation')}
          onMedicalLlm={() => navigateTo('medicalLlm')}
        />
      )
      case 'patientDashboard': return <PatientDashboard onLogout={handleLogout} />

      // Sub-modules
      case 'createPatient': return <CreatePatient userRole={userRole} onBack={handleBack} onComplete={() => navigateTo('adminDashboard', { clear: true })} />
      case 'createDoctor': return <CreateDoctor userRole={userRole} onBack={handleBack} onComplete={() => navigateTo('adminDashboard', { clear: true })} />
      case 'ecgAnalysis': return <EcgAnalysis onBack={handleBack} />
      case 'mriSegmentation': return <MriSegmentation onBack={handleBack} />
      case 'medicalLlm': return <MedicalLlm onBack={handleBack} />

      default: return <HomePage onEnter={() => navigateTo('selectRole')} onAboutClick={() => navigateTo('projectAbout')} />
    }
  }

  return (
    <div className="app">
      {renderPage()}
    </div>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
