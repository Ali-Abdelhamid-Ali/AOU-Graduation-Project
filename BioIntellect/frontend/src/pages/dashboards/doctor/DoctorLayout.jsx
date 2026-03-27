import { useMemo } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

import StaffDashboardShell from '@/components/layout/StaffDashboardShell'
import { brandingConfig } from '@/config/brandingConfig'
import { useAuth } from '@/store/AuthContext'

const viewMeta = {
  '/doctor-dashboard': {
    title: 'Doctor Dashboard',
    subtitle: `Clinical focus board for ${brandingConfig.hospitalName}`,
  },
  '/doctor-dashboard/patients': {
    title: 'My Patients',
    subtitle: 'Assigned patients, recent touchpoints, and directory access.',
  },
  '/doctor-dashboard/results': {
    title: 'Results Inbox',
    subtitle: 'Unread ECG and MRI analyses linked to your current cases.',
  },
  '/doctor-dashboard/messages': {
    title: 'Messages Center',
    subtitle: 'Unread care-team alerts, patient updates, and workflow notices.',
  },
}

const getViewMeta = (pathname) => {
  for (const [route, meta] of Object.entries(viewMeta)) {
    if (pathname === route || pathname.startsWith(route + '/')) {
      return meta
    }
  }
  return viewMeta['/doctor-dashboard']
}

export const DoctorLayout = ({ onLogout }) => {
  const { currentUser } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const currentMeta = useMemo(() => getViewMeta(location.pathname), [location.pathname])

  const navSections = useMemo(
    () => [
      {
        title: 'Clinical workflow',
        items: [
          { key: 'overview', label: 'Dashboard', description: 'Today, queue, and results', glyph: 'DB', route: '/doctor-dashboard' },
          { key: 'patients', label: 'My Patients', description: 'Assigned patients and directory access', glyph: 'PT', route: '/doctor-dashboard/patients' },
        ],
      },
      {
        title: 'Clinical tools',
        items: [
          { key: 'results', label: 'Results Inbox', description: 'Pending ECG and MRI reviews', glyph: 'RS', route: '/doctor-dashboard/results' },
          { key: 'messages', label: 'Messages', description: 'Patient and care-team notifications', glyph: 'MS', route: '/doctor-dashboard/messages' },
          { key: 'ecg', label: 'ECG Workspace', description: 'Doctor-only intake for ECG uploads', glyph: 'EC', route: '/ecg-analysis' },
          { key: 'mri', label: 'MRI Workspace', description: 'Doctor-only intake for MRI uploads', glyph: 'MR', route: '/mri-analysis' },
        ],
      },
    ],
    []
  )

  return (
    <StaffDashboardShell
      currentUser={currentUser}
      roleLabel="Doctor Workspace"
      navSections={navSections}
      onLogout={onLogout}
      headerTitle={currentMeta.title}
      headerSubtitle={currentMeta.subtitle}
      notificationCount={0}
      notificationItems={[]}
      notificationActionLabel="Open messages center"
      onNotificationAction={() => navigate('/doctor-dashboard/messages')}
    >
      <Outlet />
    </StaffDashboardShell>
  )
}

export default DoctorLayout
