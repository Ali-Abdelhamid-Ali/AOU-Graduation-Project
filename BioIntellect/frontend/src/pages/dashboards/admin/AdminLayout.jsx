import { useMemo } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

import StaffDashboardShell from '@/components/layout/StaffDashboardShell'
import { brandingConfig } from '@/config/brandingConfig'
import { ROLES } from '@/config/roles'
import { useAuth } from '@/store/AuthContext'

const viewMeta = {
  '/admin-dashboard': {
    title: 'Administrative Operations Dashboard',
    subtitle: `Production oversight for ${brandingConfig.hospitalName}`,
  },
  '/admin-dashboard/analytics': {
    title: 'Reports & Analytics',
    subtitle: 'Trend panels, telemetry, and chart-backed operational review.',
  },
  '/admin-dashboard/alerts': {
    title: 'Alerts & System Health',
    subtitle: 'Flagged audit signals, infrastructure health, and urgent notices.',
  },
  '/admin-dashboard/users': {
    title: 'User Management',
    subtitle: 'Doctors, staff, and patients under one operational table.',
  },
  '/admin-dashboard/patients': {
    title: 'Patient Directory Snapshot',
    subtitle: 'Live patient registry view inside the admin workspace shell.',
  },
  '/admin-dashboard/provisioning': {
    title: 'Provisioning Hub',
    subtitle: 'Role-aware quick actions for onboarding and operational handoff.',
  },
}

const getViewMeta = (pathname) => {
  const routes = Object.entries(viewMeta).sort(([a], [b]) => b.length - a.length)
  for (const [route, meta] of routes) {
    if (pathname === route || pathname.startsWith(route + '/')) {
      return meta
    }
  }
  return viewMeta['/admin-dashboard']
}

export const AdminLayout = ({ onLogout }) => {
  const { currentUser } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const normalizedRole = currentUser?.user_role
  const isSuperAdmin = normalizedRole === ROLES.SUPER_ADMIN

  const roleLabel = isSuperAdmin
    ? 'Super Admin Console'
    : 'Admin Workspace'

  const currentMeta = useMemo(() => getViewMeta(location.pathname), [location.pathname])

  const navSections = useMemo(
    () => [
      {
        title: 'Operations',
        items: [
          {
            key: 'overview',
            label: 'Overview',
            description: 'Live command center',
            glyph: 'OV',
            route: '/admin-dashboard',
          },
          {
            key: 'analytics',
            label: 'Reports',
            description: 'Trend panels and chart review',
            glyph: 'RP',
            route: '/admin-dashboard/analytics',
          },
          {
            key: 'alerts',
            label: 'Alerts',
            description: 'System health and audit warnings',
            glyph: 'AL',
            route: '/admin-dashboard/alerts',
          },
          {
            key: 'users',
            label: 'Users',
            description: 'Doctors, staff, and patients',
            glyph: 'US',
            route: '/admin-dashboard/users',
          },
        ],
      },
      {
        title: isSuperAdmin ? 'Governance' : 'Modules',
        items: [
          {
            key: 'patients',
            label: 'Patient Directory',
            description: 'Live registry snapshot inside the shell',
            glyph: 'PD',
            route: '/admin-dashboard/patients',
          },
          {
            key: 'provisioning',
            label: isSuperAdmin ? 'Admin Provisioning' : 'Staff Provisioning',
            description: isSuperAdmin
              ? 'Administrator creation available'
              : 'Role creation follows your permissions',
            glyph: 'PR',
            route: '/admin-dashboard/provisioning',
          },
        ],
      },
    ],
    [isSuperAdmin]
  )

  return (
    <StaffDashboardShell
      currentUser={currentUser}
      roleLabel={roleLabel}
      navSections={navSections}
      onLogout={onLogout}
      headerTitle={currentMeta.title}
      headerSubtitle={currentMeta.subtitle}
      searchPlaceholder="Search users, patients, departments, or records"
      notificationCount={0}
      notificationItems={[]}
      notificationActionLabel="Open alerts page"
      onNotificationAction={() => navigate('/admin-dashboard/alerts')}
    >
      <Outlet />
    </StaffDashboardShell>
  )
}

export default AdminLayout
