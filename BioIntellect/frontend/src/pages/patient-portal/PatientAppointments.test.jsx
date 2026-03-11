import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import { PatientAppointments } from './PatientAppointments'

const getAppointments = vi.fn()
const createAppointment = vi.fn()
const updateAppointment = vi.fn()

vi.mock('@/store/AuthContext', () => ({
  useAuth: () => ({
    currentUser: {
      id: 'patient-1',
      first_name: 'Layla',
      last_name: 'Nabil',
    },
  }),
}))

vi.mock('@/services/api', () => ({
  analyticsAPI: {
    getAppointments: (...args) => getAppointments(...args),
    createAppointment: (...args) => createAppointment(...args),
    updateAppointment: (...args) => updateAppointment(...args),
  },
}))

describe('PatientAppointments', () => {
  beforeEach(() => {
    getAppointments.mockReset()
    createAppointment.mockReset()
    updateAppointment.mockReset()
  })

  it('submits a new appointment request from the route-backed workspace', async () => {
    getAppointments
      .mockResolvedValueOnce({ success: true, data: [] })
      .mockResolvedValueOnce({
        success: true,
        data: [
          {
            id: 'case-1',
            appointment_date: '2026-03-20',
            appointment_time: '09:30',
            status: 'Scheduled',
            appointment_type: 'Follow-up',
            reason: 'Review symptoms',
          },
        ],
      })
    createAppointment.mockResolvedValue({
      success: true,
      data: { id: 'case-1' },
    })

    render(
      <MemoryRouter initialEntries={['/patient-appointments?mode=new']}>
        <Routes>
          <Route path="/patient-appointments" element={<PatientAppointments />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Request a new follow-up')).toBeTruthy()
    })

    fireEvent.change(screen.getByLabelText('Appointment date'), {
      target: { value: '2026-03-20' },
    })
    fireEvent.change(screen.getByLabelText('Appointment time'), {
      target: { value: '09:30' },
    })
    fireEvent.change(screen.getByLabelText('Appointment type'), {
      target: { value: 'MRI Follow-up' },
    })
    fireEvent.change(screen.getByLabelText('Reason'), {
      target: { value: 'Review symptoms after recent MRI.' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Book appointment' }))

    await waitFor(() => {
      expect(createAppointment).toHaveBeenCalledWith({
        appointment_date: '2026-03-20',
        appointment_time: '09:30',
        appointment_type: 'MRI Follow-up',
        reason: 'Review symptoms after recent MRI.',
        department: null,
        notes: null,
      })
    })

    await waitFor(() => {
      expect(screen.getByText('Appointment request submitted successfully.')).toBeTruthy()
    })
  })

  it('reschedules an existing appointment from search params', async () => {
    getAppointments.mockResolvedValue({
      success: true,
      data: [
        {
          id: 'case-2',
          appointment_date: '2026-03-21',
          appointment_time: '10:00',
          status: 'Scheduled',
          appointment_type: 'Follow-up',
          reason: 'Cardiology review',
          notes: 'Bring latest ECG report.',
        },
      ],
    })
    updateAppointment.mockResolvedValue({
      success: true,
      data: { id: 'case-2' },
    })

    render(
      <MemoryRouter
        initialEntries={['/patient-appointments?mode=reschedule&appointment=case-2']}
      >
        <Routes>
          <Route path="/patient-appointments" element={<PatientAppointments />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Reschedule appointment')).toBeTruthy()
    })

    const reasonField = screen.getByLabelText('Reason')
    fireEvent.change(reasonField, {
      target: { value: 'Move the cardiology review to a later slot.' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))

    await waitFor(() => {
      expect(updateAppointment).toHaveBeenCalledWith('case-2', {
        appointment_date: '2026-03-21',
        appointment_time: '10:00',
        appointment_type: 'Follow-up',
        reason: 'Move the cardiology review to a later slot.',
        department: null,
        notes: 'Bring latest ECG report.',
      })
    })
  })

  it('renders validation errors from the API as readable text instead of crashing', async () => {
    getAppointments.mockResolvedValue({ success: true, data: [] })
    createAppointment.mockRejectedValue({
      detail: [
        {
          type: 'string_too_short',
          loc: ['body', 'reason'],
          msg: 'String should have at least 1 character',
          input: '',
        },
      ],
    })

    render(
      <MemoryRouter initialEntries={['/patient-appointments?mode=new']}>
        <Routes>
          <Route path="/patient-appointments" element={<PatientAppointments />} />
        </Routes>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Request a new follow-up')).toBeTruthy()
    })

    fireEvent.change(screen.getByLabelText('Appointment date'), {
      target: { value: '2026-03-20' },
    })
    fireEvent.change(screen.getByLabelText('Reason'), {
      target: { value: 'Trigger backend validation handling.' },
    })

    fireEvent.click(screen.getByRole('button', { name: 'Book appointment' }))

    await waitFor(() => {
      expect(
        screen.getByText('body > reason: String should have at least 1 character')
      ).toBeTruthy()
    })
  })
})
