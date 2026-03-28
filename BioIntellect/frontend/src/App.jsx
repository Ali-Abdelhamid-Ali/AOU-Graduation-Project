import { Suspense, lazy } from 'react'
import { motion } from 'framer-motion'
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useNavigate,
} from 'react-router-dom'

import { AuthProvider, useAuth } from '@/store/AuthContext'
import { ROLES } from '@/config/roles'
import ErrorBoundary from '@/components/common/ErrorBoundary'
import { ProtectedRoute } from '@/components/common/ProtectedRoute'
import { ScrollToTop } from '@/components/common/ScrollToTop'
import { getDashboardHomeRoute } from '@/utils/dashboardRoutes'
import './index.css'

// ──────────────────────────── Auth Pages ────────────────────────────

const Login = lazy(() =>
  import('@/pages/auth/Login').then((m) => ({ default: m.Login }))
)

const ResetPassword = lazy(() =>
  import('@/pages/auth/ResetPassword').then((m) => ({ default: m.ResetPassword }))
)
const EmailConfirmation = lazy(() =>
  import('@/pages/auth/EmailConfirmation').then((m) => ({
    default: m.EmailConfirmation,
  }))
)
const ForcePasswordReset = lazy(() =>
  import('@/pages/auth/ForcePasswordReset').then((m) => ({
    default: m.ForcePasswordReset,
  }))
)

// ──────────────────────────── Admin Dashboard (split routes) ────────────────────────────
const AdminLayout = lazy(() =>
  import('@/pages/dashboards/admin/AdminLayout').then((m) => ({
    default: m.AdminLayout || m.default,
  }))
)
const AdminOverview = lazy(() =>
  import('@/pages/dashboards/admin/AdminOverview').then((m) => ({
    default: m.AdminOverview || m.default,
  }))
)
const AdminAnalytics = lazy(() =>
  import('@/pages/dashboards/admin/AdminAnalytics').then((m) => ({
    default: m.AdminAnalytics || m.default,
  }))
)
const AdminAlerts = lazy(() =>
  import('@/pages/dashboards/admin/AdminAlerts').then((m) => ({
    default: m.AdminAlerts || m.default,
  }))
)
const AdminUsers = lazy(() =>
  import('@/pages/dashboards/admin/AdminUsers').then((m) => ({
    default: m.AdminUsers || m.default,
  }))
)
const AdminPatients = lazy(() =>
  import('@/pages/dashboards/admin/AdminPatients').then((m) => ({
    default: m.AdminPatients || m.default,
  }))
)
const AdminProvisioning = lazy(() =>
  import('@/pages/dashboards/admin/AdminProvisioning').then((m) => ({
    default: m.AdminProvisioning || m.default,
  }))
)

// ──────────────────────────── Doctor Dashboard (split routes) ────────────────────────────
const DoctorLayout = lazy(() =>
  import('@/pages/dashboards/doctor/DoctorLayout').then((m) => ({
    default: m.DoctorLayout || m.default,
  }))
)
const DoctorOverview = lazy(() =>
  import('@/pages/dashboards/doctor/DoctorOverview').then((m) => ({
    default: m.DoctorOverview || m.default,
  }))
)
const DoctorPatients = lazy(() =>
  import('@/pages/dashboards/doctor/DoctorPatients').then((m) => ({
    default: m.DoctorPatients || m.default,
  }))
)
const DoctorResults = lazy(() =>
  import('@/pages/dashboards/doctor/DoctorResults').then((m) => ({
    default: m.DoctorResults || m.default,
  }))
)

// ──────────────────────────── Patient Dashboard ────────────────────────────
const PatientDashboard = lazy(() =>
  import('@/pages/dashboards/PatientDashboard').then((m) => ({
    default: m.PatientDashboard,
  }))
)
const PatientLayout = lazy(() =>
  import('@/components/layout/PatientLayout').then((m) => ({
    default: m.PatientLayout || m.default,
  }))
)
const PatientResults = lazy(() =>
  import('@/pages/patient-portal/PatientResults').then((m) => ({
    default: m.PatientResults,
  }))
)
const PatientResultDetails = lazy(() =>
  import('@/pages/patient-portal/PatientResultDetails').then((m) => ({
    default: m.PatientResultDetails,
  }))
)
const PatientHealthPortal = lazy(() =>
  import('@/pages/patient-portal/PatientHealthPortal').then((m) => ({
    default: m.PatientHealthPortal,
  }))
)
const PatientSecurity = lazy(() =>
  import('@/pages/patient-portal/PatientSecurity').then((m) => ({
    default: m.PatientSecurity,
  }))
)
const PatientAppointments = lazy(() =>
  import('@/pages/patient-portal/PatientAppointments').then((m) => ({
    default: m.PatientAppointments,
  }))
)

// ──────────────────────────── Clinical Tools ────────────────────────────
const EcgAnalysis = lazy(() =>
  import('@/pages/clinical-tools/EcgAnalysis').then((m) => ({
    default: m.EcgAnalysis,
  }))
)
const MriSegmentation = lazy(() =>
  import('@/pages/clinical-tools/MriSegmentation').then((m) => ({
    default: m.MriSegmentation,
  }))
)
const MedicalLlm = lazy(() =>
  import('@/pages/clinical-tools/MedicalLlm').then((m) => ({
    default: m.MedicalLlm,
  }))
)

// ──────────────────────────── Management & Public ────────────────────────────
const HomePage = lazy(() =>
  import('@/pages/public/HomePage').then((m) => ({ default: m.HomePage }))
)
const ProjectAbout = lazy(() =>
  import('@/pages/public/ProjectAbout').then((m) => ({ default: m.ProjectAbout }))
)
const NotFoundPage = lazy(() =>
  import('@/pages/public/NotFoundPage').then((m) => ({
    default: m.NotFoundPage || m.default,
  }))
)
const CreatePatient = lazy(() =>
  import('@/pages/management/CreatePatient').then((m) => ({
    default: m.CreatePatient || m.default,
  }))
)
const CreateDoctor = lazy(() =>
  import('@/pages/management/CreateDoctor').then((m) => ({
    default: m.CreateDoctor || m.default,
  }))
)
const CreateAdmin = lazy(() =>
  import('@/pages/management/CreateAdmin').then((m) => ({
    default: m.CreateAdmin || m.default,
  }))
)

// ──────────────────────────── Loading Screen ────────────────────────────
const LoadingScreen = () => (
  <div
    className="loading-screen"
    style={{
      blockSize: '100vh',
      inlineSize: '100vw',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background:
        'radial-gradient(circle at center, var(--color-surface) 0%, var(--color-background) 100%)',
      zIndex: 9999,
    }}
  >
    <div
      className="loader-pulse"
      style={{
        inlineSize: '80px',
        blockSize: '80px',
        borderRadius: '50%',
        border: '4px solid var(--color-primary-bg)',
        borderBlockStart: '4px solid var(--color-primary)',
        animation: 'spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite',
        marginBlockEnd: '2rem',
        boxShadow: '0 0 20px rgba(0, 102, 204, 0.1)',
      }}
    />
    <motion.h2
      initial={{ opacity: 0 }}
      animate={{ opacity: [0, 1, 0] }}
      transition={{ duration: 2, repeat: Infinity }}
      style={{
        color: 'var(--color-primary)',
        fontSize: '1.2rem',
        fontWeight: '600',
        letterSpacing: '4px',
        textTransform: 'uppercase',
      }}
    >
      BioIntellect
    </motion.h2>
  </div>
)

export function AppRoutes() {
  const { userRole, signOut } = useAuth()
  const navigate = useNavigate()

  const handleBack = () => navigate(-1)

  return (
    <Suspense fallback={<LoadingScreen />}>
      <Routes>
        {/* ──── Public Routes ──── */}
        <Route
          path="/"
          element={
            <HomePage
              onEnter={() => navigate('/login')}
              onAboutClick={() => navigate('/project-info')}
            />
          }
        />
        <Route
          path="/login"
          element={
            <Login
              onLoginSuccess={(role) => navigate(getDashboardHomeRoute(role))}
              onForgotPasswordClick={() => navigate('/reset-password')}
              onBack={handleBack}
            />
          }
        />
        <Route
          path="/reset-password"
          element={
            <ResetPassword
              onBack={handleBack}
              onBackToLogin={() => navigate('/login')}
              onResetSuccess={() => navigate('/login')}
            />
          }
        />
        <Route
          path="/email-confirmation"
          element={<EmailConfirmation onSignInClick={() => navigate('/login')} />}
        />
        <Route path="/project-info" element={<ProjectAbout onBack={handleBack} />} />
        <Route
          path="/force-password-reset"
          element={
            <ProtectedRoute>
              <ForcePasswordReset />
            </ProtectedRoute>
          }
        />

        {/* ──── Admin Dashboard (NESTED ROUTES — each section is its own component) ──── */}
        <Route
          element={
            <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN, ROLES.ADMIN]}>
              <AdminLayout onLogout={signOut} />
            </ProtectedRoute>
          }
        >
          <Route path="/admin-dashboard" element={<AdminOverview />} />
          <Route path="/admin-dashboard/analytics" element={<AdminAnalytics />} />
          <Route path="/admin-dashboard/alerts" element={<AdminAlerts />} />
          <Route path="/admin-dashboard/users" element={<AdminUsers />} />
          <Route path="/admin-dashboard/patients" element={<AdminPatients />} />
          <Route
            path="/admin-dashboard/provisioning"
            element={
              <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN]}>
                <AdminProvisioning />
              </ProtectedRoute>
            }
          />
        </Route>

        {/* ──── Doctor Dashboard (NESTED ROUTES — each section is its own component) ──── */}
        <Route
          element={
            <ProtectedRoute allowedRoles={[ROLES.DOCTOR]}>
              <DoctorLayout onLogout={signOut} />
            </ProtectedRoute>
          }
        >
          <Route path="/doctor-dashboard" element={<DoctorOverview />} />
          <Route path="/doctor-dashboard/patients" element={<DoctorPatients />} />
          <Route path="/doctor-dashboard/results" element={<DoctorResults />} />
        </Route>

        {/* ──── Patient Dashboard (already properly nested) ──── */}
        <Route
          element={
            <ProtectedRoute allowedRoles={[ROLES.PATIENT]}>
              <PatientLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/patient-dashboard" element={<PatientDashboard />} />
          <Route path="/patient-results" element={<PatientResults />} />
          <Route
            path="/patient-results/:resultType/:resultId"
            element={<PatientResultDetails />}
          />
          <Route path="/patient-profile" element={<PatientHealthPortal />} />
          <Route path="/patient-security" element={<PatientSecurity />} />
          <Route path="/patient-appointments" element={<PatientAppointments />} />
        </Route>

        {/* ──── Standalone Protected Routes ──── */}
        <Route
          path="/create-patient"
          element={
            <ProtectedRoute
              allowedRoles={[ROLES.SUPER_ADMIN, ROLES.ADMIN]}
            >
              <CreatePatient userRole={userRole} onBack={handleBack} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/create-doctor"
          element={
            <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN, ROLES.ADMIN]}>
              <CreateDoctor userRole={userRole} onBack={handleBack} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/create-admin"
          element={
            <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN]}>
              <CreateAdmin userRole={userRole} onBack={handleBack} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/ecg-analysis"
          element={
            <ProtectedRoute allowedRoles={[ROLES.ADMIN, ROLES.DOCTOR]}>
              <EcgAnalysis onBack={handleBack} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mri-analysis"
          element={
            <ProtectedRoute allowedRoles={[ROLES.ADMIN, ROLES.DOCTOR]}>
              <MriSegmentation onBack={handleBack} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mri-segmentation"
          element={
            <ProtectedRoute allowedRoles={[ROLES.ADMIN, ROLES.DOCTOR]}>
              <MriSegmentation onBack={handleBack} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/medical-llm"
          element={
            <ProtectedRoute allowedRoles={[ROLES.SUPER_ADMIN, ROLES.ADMIN, ROLES.DOCTOR]}>
              <MedicalLlm onBack={handleBack} />
            </ProtectedRoute>
          }
        />

        {/* ──── 404 Catch-all ──── */}
        <Route path="*" element={<NotFoundPage />} />
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
