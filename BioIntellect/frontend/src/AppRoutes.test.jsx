import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'

import { AppRoutes } from '@/App'

const authState = {
  userRole: 'doctor',
  signOut: vi.fn(),
  mustResetPassword: false,
  isAuthenticated: true,
  isLoading: false,
}

vi.mock('@/store/AuthContext', () => ({
  useAuth: () => authState,
}))

vi.mock('@/pages/clinical-tools/EcgAnalysis', () => ({
  EcgAnalysis: () => <div>ECG Workspace</div>,
}))

vi.mock('@/pages/clinical-tools/MriSegmentation', () => ({
  MriSegmentation: () => <div>MRI Workspace</div>,
}))

vi.mock('@/pages/clinical-tools/MedicalLlm', () => ({
  MedicalLlm: () => <div>Medical LLM Workspace</div>,
}))

vi.mock('@/pages/dashboards/DoctorDashboard', () => ({
  DoctorDashboard: () => <div>Doctor Dashboard</div>,
}))

vi.mock('@/components/layout/PatientLayout', () => ({
  PatientLayout: () => <div>Patient Layout</div>,
  default: () => <div>Patient Layout</div>,
}))

describe('clinical tool routing', () => {
  it.each([
    ['/ecg-analysis', 'ECG Workspace'],
    ['/mri-analysis', 'MRI Workspace'],
    ['/medical-llm', 'Medical LLM Workspace'],
  ])(
    'opens %s for doctors without falling back to the dashboard',
    async (initialPath, expectedText) => {
      render(
        <MemoryRouter initialEntries={[initialPath]}>
          <AppRoutes />
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText(expectedText)).toBeInTheDocument()
      })

      expect(screen.queryByText('Doctor Dashboard')).not.toBeInTheDocument()
      expect(screen.queryByText('Patient Layout')).not.toBeInTheDocument()
    }
  )
})
