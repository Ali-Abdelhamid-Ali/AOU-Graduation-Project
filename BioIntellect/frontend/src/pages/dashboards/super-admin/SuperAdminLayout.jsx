import { useEffect, useMemo, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

import StaffDashboardShell from '@/components/layout/StaffDashboardShell'
import { brandingConfig } from '@/config/brandingConfig'
import { dashboardAPI } from '@/services/api'
import { useAuth } from '@/store/AuthContext'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'

const viewMeta = {
  '/super-admin': {
    title: 'Super Admin Operations Console',
    subtitle: `Cross-tenant governance for ${brandingConfig.hospitalName}`,
  },
  '/super-admin/analytics': {
    title: 'Super Admin Analytics',
    subtitle: 'Global trends, compliance telemetry, and usage analytics.',
  },
  '/super-admin/alerts': {
    title: 'Critical Alerts & Health',
    subtitle: 'Infrastructure, audit, and security alerts across modules.',
  },
  '/super-admin/users': {
    title: 'Identity & Access Management',
    subtitle: 'Review and govern administrators, doctors, and patients.',
  },
  '/super-admin/patients': {
    title: 'Patient Registry Governance',
    subtitle: 'Operational view of patient records and demographic coverage.',
  },
  '/super-admin/provisioning': {
    title: 'Privileged Provisioning',
    subtitle: 'Create administrator, doctor, and super admin accounts.',
  },
}

const getViewMeta = (pathname) => {
  const routes = Object.entries(viewMeta).sort(([a], [b]) => b.length - a.length)
  for (const [route, meta] of routes) {
    if (pathname === route || pathname.startsWith(route + '/')) {
      return meta
    }
  }
  return viewMeta['/super-admin']
}

export const SuperAdminLayout = ({ onLogout }) => {
  const { currentUser } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [notificationItems, setNotificationItems] = useState([])
  const [notificationCount, setNotificationCount] = useState(0)

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
        console.warn(getApiErrorMessage(err, 'Failed to load super admin notifications.'))
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
            description: 'Global command center',
            glyph: 'OV',
            route: '/super-admin',
          },
          {
            key: 'analytics',
            label: 'Analytics',
            description: 'Cross-module trends and diagnostics',
            glyph: 'AN',
            route: '/super-admin/analytics',
          },
          {
            key: 'alerts',
            label: 'Alerts',
            description: 'Security and platform health',
            glyph: 'AL',
            route: '/super-admin/alerts',
          },
          {
            key: 'users',
            label: 'Users',
            description: 'Identity and access governance',
            glyph: 'US',
            route: '/super-admin/users',
          },
        ],
      },
      {
        title: 'Governance',
        items: [
          {
            key: 'patients',
            label: 'Patient Directory',
            description: 'Cross-facility registry insight',
            glyph: 'PD',
            route: '/super-admin/patients',
          },
          {
            key: 'provisioning',
            label: 'Provisioning',
            description: 'Create admin, doctor, and super admin identities',
            glyph: 'PR',
            route: '/super-admin/provisioning',
          },
        ],
      },
    ],
    []
  )

  return (
    <StaffDashboardShell
      currentUser={currentUser}
      roleLabel="Super Admin Console"
      navSections={navSections}
      onLogout={onLogout}
      headerTitle={currentMeta.title}
      headerSubtitle={currentMeta.subtitle}
      searchPlaceholder="Search users, records, modules, and governance events"
      notificationCount={notificationCount}
      notificationItems={notificationItems}
      notificationActionLabel="Open alerts"
      onNotificationAction={() => navigate('/super-admin/alerts')}
    >
      <Outlet />
    </StaffDashboardShell>
  )
}

export default SuperAdminLayout
