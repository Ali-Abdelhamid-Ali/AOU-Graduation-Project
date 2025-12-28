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
const CreatePatient = lazy(() => import('./pages/CreatePatient'))
const CreateDoctor = lazy(() => import('./pages/CreateDoctor'))
const CreateAdmin = lazy(() => import('./pages/CreateAdmin'))
const ProjectAbout = lazy(() => import('./pages/ProjectAbout').then(m => ({ default: m.ProjectAbout })))
const EcgAnalysis = lazy(() => import('./pages/EcgAnalysis').then(m => ({ default: m.EcgAnalysis })))
const MriSegmentation = lazy(() => import('./pages/MriSegmentation').then(m => ({ default: m.MriSegmentation })))
const MedicalLlm = lazy(() => import('./pages/MedicalLlm').then(m => ({ default: m.MedicalLlm })))
const ForcePasswordReset = lazy(() => import('./pages/ForcePasswordReset').then(m => ({ default: m.ForcePasswordReset })))
const PatientLayout = lazy(() => import('./components/PatientLayout').then(m => ({ default: m.PatientLayout })))
const PatientResults = lazy(() => import('./pages/PatientResults').then(m => ({ default: m.PatientResults })))
const PatientProfile = lazy(() => import('./pages/PatientProfile').then(m => ({ default: m.PatientProfile })))
const PatientSecurity = lazy(() => import('./pages/PatientSecurity').then(m => ({ default: m.PatientSecurity })))
const PatientAppointments = lazy(() => import('./pages/PatientAppointments').then(m => ({ default: m.PatientAppointments })))

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
              // Standardize roles using ROLES constants or explicit checks
              if (['admin', 'administrator', 'super_admin'].includes(role.toLowerCase())) {
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
              const r = role?.toLowerCase();
              if (['super_admin', 'administrator', 'admin', 'doctor', 'nurse'].includes(r)) {
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
        <Route path="/force-password-reset" element={
          <ProtectedRoute>
            <ForcePasswordReset />
          </ProtectedRoute>
        } />

        {/* Protected Dashboard Routes (RBAC) */}
        <Route path="/admin-dashboard" element={
          <ProtectedRoute allowedRoles={['super_admin', 'administrator', 'doctor', 'nurse']}>
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

        <Route element={
          <ProtectedRoute allowedRoles={['patient']}>
            <PatientLayout />
          </ProtectedRoute>
        }>
          <Route path="/patient-dashboard" element={<PatientDashboard />} />
          <Route path="/patient-results" element={<PatientResults />} />
          <Route path="/patient-profile" element={<PatientProfile />} />
          <Route path="/patient-security" element={<PatientSecurity />} />
          <Route path="/patient-appointments" element={<PatientAppointments />} />

          {/* AI Modules Integrated within Patient Portal */}
          <Route path="/ecg-analysis" element={<EcgAnalysis onBack={handleBack} />} />
          <Route path="/mri-segmentation" element={<MriSegmentation onBack={handleBack} />} />
          <Route path="/medical-llm" element={<MedicalLlm onBack={handleBack} />} />
        </Route>

        {/* Sub-modules (Protected) */}
        <Route path="/create-patient" element={
          <ProtectedRoute allowedRoles={['super_admin', 'administrator', 'doctor', 'nurse']}>
            <CreatePatient userRole={userRole} onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/create-doctor" element={
          <ProtectedRoute allowedRoles={['super_admin', 'administrator']}>
            <CreateDoctor userRole={userRole} onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/create-admin" element={
          <ProtectedRoute allowedRoles={['super_admin', 'administrator']}>
            <CreateAdmin userRole={userRole} onBack={handleBack} />
          </ProtectedRoute>
        } />

        {/* Keep the standalone protected routes for non-patient roles if needed, 
            or they will use the global handlers. For patients, they are handled above. */}
        <Route path="/ecg-analysis" element={
          <ProtectedRoute allowedRoles={['super_admin', 'administrator', 'doctor', 'nurse']}>
            <EcgAnalysis onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/mri-segmentation" element={
          <ProtectedRoute allowedRoles={['super_admin', 'administrator', 'doctor', 'nurse']}>
            <MriSegmentation onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/medical-llm" element={
          <ProtectedRoute allowedRoles={['super_admin', 'administrator', 'doctor', 'nurse']}>
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

