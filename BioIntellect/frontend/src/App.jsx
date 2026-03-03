import { Suspense, lazy, useEffect } from 'react'
import { motion } from 'framer-motion'
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from '@/store/AuthContext'
import { ROLES, ROLE_ALIAS_MAP } from '@/config/roles'
import ErrorBoundary from '@/components/common/ErrorBoundary'
import { ProtectedRoute } from '@/components/common/ProtectedRoute'
import { ScrollToTop } from '@/components/common/ScrollToTop'
import './index.css'

// Lazy Load Pages for Production Performance (FCP/TTI Optimization)
// Lazy Load Pages sorted by domain
// Auth
const SelectRole = lazy(() => import('@/pages/auth/SelectRole').then(m => ({ default: m.SelectRole })))
const Login = lazy(() => import('@/pages/auth/Login').then(m => ({ default: m.Login })))
const SignUp = lazy(() => import('@/pages/auth/SignUp').then(m => ({ default: m.SignUp })))
const ResetPassword = lazy(() => import('@/pages/auth/ResetPassword').then(m => ({ default: m.ResetPassword })))
const EmailConfirmation = lazy(() => import('@/pages/auth/EmailConfirmation').then(m => ({ default: m.EmailConfirmation })))
const ForcePasswordReset = lazy(() => import('@/pages/auth/ForcePasswordReset').then(m => ({ default: m.ForcePasswordReset })))

// Dashboards
const AdminDashboard = lazy(() => import('@/pages/dashboards/AdminDashboard').then(m => ({ default: m.AdminDashboard })))
const PatientDashboard = lazy(() => import('@/pages/dashboards/PatientDashboard').then(m => ({ default: m.PatientDashboard })))
const PatientLayout = lazy(() => import('@/components/layout/PatientLayout').then(m => ({ default: m.PatientLayout || m.default })))

// Patient Portal
const PatientResults = lazy(() => import('@/pages/patient-portal/PatientResults').then(m => ({ default: m.PatientResults })))
const PatientHealthPortal = lazy(() => import('@/pages/patient-portal/PatientHealthPortal').then(m => ({ default: m.PatientHealthPortal })))
const PatientSecurity = lazy(() => import('@/pages/patient-portal/PatientSecurity').then(m => ({ default: m.PatientSecurity })))
const PatientAppointments = lazy(() => import('@/pages/patient-portal/PatientAppointments').then(m => ({ default: m.PatientAppointments })))

// Clinical Tools
const EcgAnalysis = lazy(() => import('@/pages/clinical-tools/EcgAnalysis').then(m => ({ default: m.EcgAnalysis })))
const MriSegmentation = lazy(() => import('@/pages/clinical-tools/MriSegmentation').then(m => ({ default: m.MriSegmentation })))
const MedicalLlm = lazy(() => import('@/pages/clinical-tools/MedicalLlm').then(m => ({ default: m.MedicalLlm })))

// Management
const PatientDirectory = lazy(() => import('@/pages/management/PatientDirectory').then(m => ({ default: m.PatientDirectory })))
// Public
const HomePage = lazy(() => import('@/pages/public/HomePage').then(m => ({ default: m.HomePage })))
const ProjectAbout = lazy(() => import('@/pages/public/ProjectAbout').then(m => ({ default: m.ProjectAbout })))
const CreatePatient = lazy(() => import('@/pages/management/CreatePatient').then(m => ({ default: m.CreatePatient || m.default })))
const CreateDoctor = lazy(() => import('@/pages/management/CreateDoctor').then(m => ({ default: m.CreateDoctor || m.default })))
const CreateAdmin = lazy(() => import('@/pages/management/CreateAdmin').then(m => ({ default: m.CreateAdmin || m.default })))

const LoadingScreen = () => (
  <div className="loading-screen" style={{
    height: '100vh',
    width: '100vw',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'radial-gradient(circle at center, var(--color-surface) 0%, var(--color-background) 100%)',
    zIndex: 9999
  }}>
    <div className="loader-pulse" style={{
      width: '80px',
      height: '80px',
      borderRadius: '50%',
      border: '4px solid var(--color-primary-bg)',
      borderTop: '4px solid var(--color-primary)',
      animation: 'spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite',
      marginBottom: '2rem',
      boxShadow: '0 0 20px rgba(0, 102, 204, 0.1)'
    }}></div>
    <motion.h2
      initial={{ opacity: 0 }}
      animate={{ opacity: [0, 1, 0] }}
      transition={{ duration: 2, repeat: Infinity }}
      style={{
        color: 'var(--color-primary)',
        fontSize: '1.2rem',
        fontWeight: '600',
        letterSpacing: '4px',
        textTransform: 'uppercase'
      }}
    >
      BioIntellect
    </motion.h2>
  </div>
)

import { useNavigate } from 'react-router-dom'

function AppRoutes() {
  const { userRole, signOut, mustResetPassword, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleBack = () => navigate(-1)

  // ━━━━ MANDATORY SECURITY PROTOCOL ENFORCEMENT ━━━━
  // If the user must reset their password, they are locked into the ForcePasswordReset page.
  useEffect(() => {
    if (isAuthenticated && mustResetPassword && location.pathname !== '/force-password-reset') {
      console.warn("🔒 [SECURITY]: Mandatory password reset required. Redirecting...");
      navigate('/force-password-reset', { replace: true });
    }
  }, [isAuthenticated, mustResetPassword, location.pathname, navigate]);

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
              const normalized = ROLE_ALIAS_MAP[role.toLowerCase()]
              if ([ROLES.ADMIN, ROLES.SUPER_ADMIN].includes(normalized)) {
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
              const r = ROLE_ALIAS_MAP[role?.toLowerCase()];
              if ([ROLES.SUPER_ADMIN, ROLES.ADMIN, ROLES.DOCTOR, ROLES.NURSE].includes(r)) {
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
          <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN, ROLES.ADMIN, ROLES.DOCTOR, ROLES.NURSE]}>
            <AdminDashboard
              userRole={userRole}
              onLogout={signOut}
              onCreatePatient={() => navigate('/create-patient')}
              onCreateDoctor={() => navigate('/create-doctor')}
              onCreateAdmin={() => navigate('/create-admin')}
              onEcgAnalysis={() => navigate('/ecg-analysis')}
              onMriSegmentation={() => navigate('/mri-segmentation')}
              onMedicalLlm={() => navigate('/medical-llm')}
              onPatientDirectory={() => navigate('/patient-directory')}
            />
          </ProtectedRoute>
        } />

        <Route element={
          <ProtectedRoute allowedRoles={[ROLES.PATIENT]}>
            <PatientLayout />
          </ProtectedRoute>
        }>
          <Route path="/patient-dashboard" element={<PatientDashboard />} />
          <Route path="/patient-results" element={<PatientResults />} />
          <Route path="/patient-profile" element={<PatientHealthPortal />} />
          <Route path="/patient-security" element={<PatientSecurity />} />
          <Route path="/patient-appointments" element={<PatientAppointments />} />

          {/* AI Modules Integrated within Patient Portal */}
          <Route path="/ecg-analysis" element={<EcgAnalysis onBack={handleBack} />} />
          <Route path="/mri-segmentation" element={<MriSegmentation onBack={handleBack} />} />
          <Route path="/medical-llm" element={<MedicalLlm onBack={handleBack} />} />
        </Route>

        {/* Sub-modules (Protected) */}
        <Route path="/patient-directory" element={
          <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN, ROLES.ADMIN, ROLES.DOCTOR, ROLES.NURSE]}>
            <PatientDirectory onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/create-patient" element={
          <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN, ROLES.ADMIN, ROLES.DOCTOR, ROLES.NURSE]}>
            <CreatePatient userRole={userRole} onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/create-doctor" element={
          <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN, ROLES.ADMIN]}>
            <CreateDoctor userRole={userRole} onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/create-admin" element={
          <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN, ROLES.ADMIN]}>
            <CreateAdmin userRole={userRole} onBack={handleBack} />
          </ProtectedRoute>
        } />

        {/* Keep the standalone protected routes for non-patient roles if needed, 
            or they will use the global handlers. For patients, they are handled above. */}
        <Route path="/ecg-analysis" element={
          <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN, ROLES.ADMIN, ROLES.DOCTOR, ROLES.NURSE]}>
            <EcgAnalysis onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/mri-segmentation" element={
          <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN, ROLES.ADMIN, ROLES.DOCTOR, ROLES.NURSE]}>
            <MriSegmentation onBack={handleBack} />
          </ProtectedRoute>
        } />

        <Route path="/medical-llm" element={
          <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN, ROLES.ADMIN, ROLES.DOCTOR, ROLES.NURSE]}>
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

