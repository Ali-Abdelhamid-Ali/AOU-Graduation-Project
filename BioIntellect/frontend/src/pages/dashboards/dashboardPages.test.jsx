import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AdminDashboard } from '@/pages/dashboards/AdminDashboard'
import { DoctorDashboard } from '@/pages/dashboards/DoctorDashboard'
import { getDashboardHomeRoute } from '@/utils/dashboardRoutes'

const navigateMock = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => navigateMock,
  }
})

vi.mock('@/store/AuthContext', () => ({
  useAuth: () => ({
    currentUser: {
      first_name: 'Mina',
      last_name: 'Youssef',
      hospital_name: 'Saudi German Hospital',
      specialty_name: 'Cardiology',
    },
  }),
}))

const getAdminOverview = vi.fn()
const getDoctorOverview = vi.fn()
const listUsers = vi.fn()

vi.mock('@/services/api', () => ({
  dashboardAPI: {
    getAdminOverview: (...args) => getAdminOverview(...args),
    getDoctorOverview: (...args) => getDoctorOverview(...args),
  },
  usersAPI: {
    list: (...args) => listUsers(...args),
  },
}))

describe('dashboard route mapping', () => {
  it('routes doctors and staff to the correct dashboard home', () => {
    expect(getDashboardHomeRoute('doctor')).toBe('/doctor-dashboard')
    expect(getDashboardHomeRoute('admin')).toBe('/admin-dashboard')
    expect(getDashboardHomeRoute('administrator')).toBe('/admin-dashboard')
    expect(getDashboardHomeRoute('patient')).toBe('/patient-dashboard')
  })
})

describe('dashboard pages', () => {
  beforeEach(() => {
    navigateMock.mockReset()
    getAdminOverview.mockReset()
    getDoctorOverview.mockReset()
    listUsers.mockReset()
  })

  it('renders admin dashboard with unavailable capability panels and user table', async () => {
    getAdminOverview.mockResolvedValue({
      data: {
        stats: {
          patients: { label: 'Patients', value: 10, helper: '2 active users', available: true, tone: 'info' },
          doctors: { label: 'Doctors', value: 4, helper: '12 medical cases tracked', available: true, tone: 'success' },
          appointments: { label: 'Appointments', value: null, helper: 'Scheduling module not configured in the current schema.', available: false, tone: 'warning' },
          revenue: { label: 'Revenue', value: null, helper: 'Billing and payments module not configured in the current schema.', available: false, tone: 'warning' },
        },
        charts: {
          daily_appointments_trend: { available: false, message: 'Appointment scheduling module not configured.' },
          revenue_by_month: { available: false, message: 'Billing and payments module not configured.' },
          disease_distribution: {
            available: true,
            message: 'Distribution derived from medical_cases diagnosis fields.',
            data: [
              { label: 'I48', value: 6 },
              { label: 'G93', value: 2 },
            ],
          },
        },
        recent_activity: [],
        system_health: {
          status: 'healthy',
          summary: 'Operational telemetry pulled from audit logs and runtime health checks.',
          metrics: [{ label: 'Database', value: 'Healthy', tone: 'success' }],
        },
        alerts: [],
        capabilities: {
          appointments: false,
          billing: false,
          messaging: true,
          disease_distribution: true,
        },
      },
    })

    listUsers.mockImplementation(async (type) => {
      if (type === 'patients') return [{ id: 'patient-1', first_name: 'Nour', last_name: 'Ali', medical_record_number: 'MRN-1', hospital_name: 'Saudi German Hospital', is_active: true }]
      if (type === 'doctors') return [{ id: 'doctor-1', first_name: 'Khaled', last_name: 'Hassan', specialty: 'Cardiology', hospital_name: 'Saudi German Hospital', is_active: true }]
      return []
    })

    render(<AdminDashboard onLogout={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Administrative Operations Dashboard')).toBeTruthy()
    })

    expect(screen.getByText('Capability disabled')).toBeTruthy()
    expect(screen.getByText('User Management')).toBeTruthy()
    expect(screen.getByText('Nour Ali')).toBeTruthy()
    expect(screen.getByText('Khaled Hassan')).toBeTruthy()
  })

  it('renders doctor dashboard with schedule unavailable state and pending result data', async () => {
    getDoctorOverview.mockResolvedValue({
      data: {
        today_schedule: {
          available: false,
          message: 'Scheduling module not configured.',
          data: [],
        },
        patient_queue: [
          {
            id: 'queue-1',
            patient_name: 'Layla Nabil',
            case_number: 'CASE-1001',
            priority: 'high',
            wait_time_label: '20 min ago',
          },
        ],
        quick_stats: {
          total_patients: { label: 'Total Patients', value: 1, helper: 'Unique patients associated with your assigned cases.' },
          pending_reports: { label: 'Pending Reports', value: 1, helper: 'Unread ECG and MRI analyses waiting for review.' },
          unread_messages: { label: 'Unread Messages', value: 3, helper: 'Unread notifications and care-team alerts.' },
        },
        recent_patients: [{ id: 'patient-1', name: 'Layla Nabil', mrn: 'MRN-44', last_visit_label: '1 hr ago' }],
        pending_results: [
          {
            id: 'result-1',
            type: 'ECG',
            patient_name: 'Layla Nabil',
            summary: 'Atrial flutter',
            case_number: 'CASE-1001',
            time_ago: '15 min ago',
          },
        ],
        notifications: [
          {
            id: 'notification-1',
            title: 'Unread message',
            message: 'Patient uploaded new ECG result',
            priority: 'high',
            time_ago: '10 min ago',
          },
        ],
        capabilities: {
          appointments: false,
          billing: false,
          messaging: true,
          disease_distribution: false,
        },
      },
    })

    render(<DoctorDashboard onLogout={vi.fn()} />)

    await waitFor(() => {
      expect(screen.getByText('Doctor Dashboard')).toBeTruthy()
    })

    expect(screen.getByText('Scheduling module not configured')).toBeTruthy()
    expect(screen.getByText('Layla Nabil')).toBeTruthy()
    expect(screen.getByText('Atrial flutter')).toBeTruthy()
    expect(screen.getByText('Unread message')).toBeTruthy()
  })
})
