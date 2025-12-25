import { Suspense, lazy } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ErrorBoundary from './components/ErrorBoundary'
import { ProtectedRoute } from './components/ProtectedRoute'
import { ScrollToTop } from './components/ScrollToTop'
import './index.css'

// Lazy Load Pages for Production Performance (FCP/TTI Optimization)
const SelectRole = lazy(() => import('./pages/SelectRole').then(m => ({ default: m.SelectRole })))
const Login = lazy(() => import('./pages/Login').then(m => ({ default: m.Login })))
const SignUp = lazy(() => import('./pages/SignUp').then(m => ({ default: m.SignUp })))
const ResetPassword = lazy(() => import('./pages/ResetPassword').then(m => ({ default: m.ResetPassword })))
const EmailConfirmation = lazy(() => import('./pages/EmailConfirmation').then(m => ({ default: m.EmailConfirmation })))
const HomePage = lazy(() => import('./pages/HomePage').then(m => ({ default: m.HomePage })))
const AdminDashboard = lazy(() => import('./pages/AdminDashboard').then(m => ({ default: m.AdminDashboard })))
const PatientDashboard = lazy(() => import('./pages/PatientDashboard').then(m => ({ default: m.PatientDashboard })))
const CreatePatient = lazy(() => import('./pages/CreatePatient').then(m => ({ default: m.CreatePatient })))
const CreateDoctor = lazy(() => import('./pages/CreateDoctor').then(m => ({ default: m.CreateDoctor })))
const CreateAdmin = lazy(() => import('./pages/CreateAdmin').then(m => ({ default: m.CreateAdmin })))
const ProjectAbout = lazy(() => import('./pages/ProjectAbout').then(m => ({ default: m.ProjectAbout })))
const EcgAnalysis = lazy(() => import('./pages/EcgAnalysis').then(m => ({ default: m.EcgAnalysis })))
const MriSegmentation = lazy(() => import('./pages/MriSegmentation').then(m => ({ default: m.MriSegmentation })))
const MedicalLlm = lazy(() => import('./pages/MedicalLlm').then(m => ({ default: m.MedicalLlm })))

const LoadingScreen = () => (
  <div className="loading-screen" style={{
    height: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--color-background)',
    color: 'var(--color-primary)',
    fontFamily: 'var(--font-family-mono)'
  }}>
    INITIALIZING_BIOINTELLECT_MODULES...
  </div>
)

import { useNavigate } from 'react-router-dom'

function AppRoutes() {
  const { userRole, signOut } = useAuth()
  const navigate = useNavigate()

  const handleBack = () => navigate(-1)

  return (
    <Suspense fallback={<LoadingScreen />}>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={
          <HomePage
            onEnter={() => navigate('/select-role')}
            onAboutClick={() => navigate('/project-info')}
          />
        } />

        <Route path="/select-role" element={
          <SelectRole
            onRoleSelected={(role) => {
              if (role === 'administrator') {
                navigate('/signup')
              } else {
                navigate('/login')
              }
            }}
            onBack={handleBack}
          />
        } />

        <Route path="/login" element={
          <Login
            onLoginSuccess={(role) => {
              if (role === 'administrator' || role === 'doctor' || role === 'physician') {
                navigate('/admin-dashboard')
              } else {
                navigate('/patient-dashboard')
              }
            }}
            onSignUpClick={() => navigate('/signup')}
            onForgotPasswordClick={() => navigate('/reset-password')}
            onBack={handleBack}
          />
        } />

        <Route path="/signup" element={
          <SignUp
            onSignUpSuccess={() => navigate('/login')}
            onLoginClick={() => navigate('/login')}
            onBack={handleBack}
          />
        } />

        <Route path="/reset-password" element={
          <ResetPassword
            onBack={handleBack}
            onBackToLogin={() => navigate('/login')}
            onResetSuccess={() => navigate('/login')}
          />
        } />

        <Route path="/email-confirmation" element={<EmailConfirmation />} />
        <Route path="/project-info" element={<ProjectAbout onBack={handleBack} />} />

        {/* Protected Dashboard Routes (RBAC) */}
        <Route path="/admin-dashboard" element={
          <ProtectedRoute allowedRoles={['administrator', 'doctor', 'physician']}>
            <AdminDashboard
              userRole={userRole}
              onLogout={signOut}
              onCreatePatient={() => navigate('/create-patient')}
              onCreateDoctor={() => navigate('/create-doctor')}
              onCreateAdmin={() => navigate('/create-admin')}
              onEcgAnalysis={() => navigate('/ecg-analysis')}
              onMriSegmentation={() => navigate('/mri-segmentation')}
              onMedicalLlm={() => navigate('/medical-llm')}
            />
          </ProtectedRoute>
        } />

        <Route path="/patient-dashboard" element={
          <ProtectedRoute allowedRoles={['patient']}>
            <PatientDashboard
              onLogout={signOut}
              onEcgAnalysis={() => navigate('/ecg-analysis')}
              onMriSegmentation={() => navigate('/mri-segmentation')}
              onMedicalLlm={() => navigate('/medical-llm')}
            />
          </ProtectedRoute>
        } />

        {/* Sub-modules (Protected) */}
        <Route path="/create-patient" element={
          <ProtectedRoute allowedRoles={['administrator', 'doctor', 'physician']}>
            <CreatePatient userRole={userRole} onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/create-doctor" element={
          <ProtectedRoute allowedRoles={['administrator']}>
            <CreateDoctor userRole={userRole} onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/create-admin" element={
          <ProtectedRoute allowedRoles={['administrator']}>
            <CreateAdmin userRole={userRole} onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/ecg-analysis" element={
          <ProtectedRoute allowedRoles={['administrator', 'doctor', 'physician', 'patient']}>
            <EcgAnalysis onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/mri-segmentation" element={
          <ProtectedRoute allowedRoles={['administrator', 'doctor', 'physician', 'patient']}>
            <MriSegmentation onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/medical-llm" element={
          <ProtectedRoute allowedRoles={['administrator', 'doctor', 'physician', 'patient']}>
            <MedicalLlm onBack={handleBack} />
          </ProtectedRoute>
        } />

        {/* Catch-all Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}


function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <ScrollToTop />
          <div className="app">
            <AppRoutes />
          </div>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App

