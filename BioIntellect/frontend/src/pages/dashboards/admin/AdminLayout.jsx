import { useEffect, useMemo, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

import StaffDashboardShell from '@/components/layout/StaffDashboardShell'
import { brandingConfig } from '@/config/brandingConfig'
import { ROLES } from '@/config/roles'
import { dashboardAPI } from '@/services/api'
import { useAuth } from '@/store/AuthContext'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'

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
  const [notificationItems, setNotificationItems] = useState([])
  const [notificationCount, setNotificationCount] = useState(0)

  const normalizedRole = currentUser?.user_role
  const isSuperAdmin = normalizedRole === ROLES.SUPER_ADMIN

  const roleLabel = isSuperAdmin
    ? 'Super Admin Console'
    : 'Admin Workspace'

  const currentMeta = useMemo(() => getViewMeta(location.pathname), [location.pathname])

  useEffect(() => {
    let cancelled = false

    const loadNotifications = async () => {
      try {
        const response = await dashboardAPI.getAdminOverview()
        const overview = response?.data || {}
        const alerts = Array.isArray(overview.alerts) ? overview.alerts : []
        const activity = Array.isArray(overview.recent_activity) ? overview.recent_activity : []

        const items = [
          ...alerts.map((item) => ({
            id: `alert-${item.id || Math.random().toString(36).slice(2)}`,
            title: item.title || 'Alert',
            message: item.message || '',
            time: item.time_ago || item.timestamp || 'Recent',
          })),
          ...activity.map((item) => ({
            id: `activity-${item.id || Math.random().toString(36).slice(2)}`,
            title: item.title || 'Activity',
            message: item.message || '',
            time: item.time_ago || item.timestamp || 'Recent',
          })),
        ].slice(0, 6)

        if (!cancelled) {
          setNotificationItems(items)
          setNotificationCount(alerts.length)
        }
      } catch (err) {
        if (!cancelled) {
          setNotificationItems([])
          setNotificationCount(0)
        }
        console.warn(getApiErrorMessage(err, 'Failed to load admin notifications.'))
      }
    }

    loadNotifications()
    return () => {
      cancelled = true
    }
  }, [])

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
          ...(isSuperAdmin
            ? [
                {
                  key: 'provisioning',
                  label: 'Admin Provisioning',
                  description: 'Administrator creation available',
                  glyph: 'PR',
                  route: '/admin-dashboard/provisioning',
                },
              ]
            : []),
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
      notificationCount={notificationCount}
      notificationItems={notificationItems}
      notificationActionLabel="Open alerts page"
      onNotificationAction={() => navigate('/admin-dashboard/alerts')}
    >
      <Outlet />
    </StaffDashboardShell>
  )
}

export default AdminLayout
