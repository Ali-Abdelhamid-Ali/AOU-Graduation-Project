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
  '/doctor-dashboard/schedule': {
    title: 'Schedule Board',
    subtitle: 'Timeline and slot planning from trusted appointment data.',
  },
  '/doctor-dashboard/queue': {
    title: 'Patient Queue',
    subtitle: 'Open, pending, and high-priority cases requiring immediate review.',
  },
  '/doctor-dashboard/patients': {
    title: 'My Patients',
    subtitle: 'Assigned patients, recent touchpoints, and directory access.',
  },
  '/doctor-dashboard/results': {
    title: 'Results Inbox',
    subtitle: 'Unread ECG and MRI analyses linked to your current cases.',
  },
  '/doctor-dashboard/reports': {
    title: 'Report Composer',
    subtitle: 'Narrative drafting and review handoff without leaving the doctor workspace.',
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
          { key: 'queue', label: 'Patient Queue', description: 'Open, pending, and high-priority cases', glyph: 'PQ', route: '/doctor-dashboard/queue' },
          { key: 'patients', label: 'My Patients', description: 'Assigned patients and directory access', glyph: 'PT', route: '/doctor-dashboard/patients' },
          { key: 'schedule', label: 'Schedule', description: 'Timeline, slots, and clinic rhythm', glyph: 'SC', route: '/doctor-dashboard/schedule' },
        ],
      },
      {
        title: 'Clinical tools',
        items: [
          { key: 'results', label: 'Results Inbox', description: 'Pending ECG and MRI reviews', glyph: 'RS', route: '/doctor-dashboard/results' },
          { key: 'reports', label: 'Report Composer', description: 'Narrative drafting and sign-off prep', glyph: 'RP', route: '/doctor-dashboard/reports' },
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
      searchPlaceholder="Search patient, MRN, case, ECG, or MRI"
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
