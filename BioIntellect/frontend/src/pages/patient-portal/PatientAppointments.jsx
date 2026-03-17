import { useCallback, useEffect, useLayoutEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useSearchParams } from 'react-router-dom'

import { Skeleton } from '@/components/ui/Skeleton'
import SkeletonText from '@/components/ui/SkeletonText'
import { analyticsAPI } from '@/services/api'
import { useAuth } from '@/store/AuthContext'
import { getApiErrorMessage } from '@/utils/apiErrorUtils'
import styles from './PatientAppointments.module.css'

const normalizeStatus = (value) => {
  const text = String(value || 'Scheduled')
    .replace(/_/g, ' ')
    .trim()
  return text
    ? text.replace(/\w\S*/g, (part) => part[0].toUpperCase() + part.slice(1).toLowerCase())
    : 'Scheduled'
}

const normalizeAppointment = (appointment = {}) => ({
  id: appointment.id,
  caseId: appointment.case_id,
  doctor: appointment.doctors
    ? `Dr. ${appointment.doctors.first_name} ${appointment.doctors.last_name}`
    : 'Clinical Staff',
  specialty:
    appointment.doctors?.specialty ||
    appointment.doctors?.qualification ||
    appointment.department ||
    'Medical Specialist',
  date: appointment.appointment_date,
  time: appointment.appointment_time || '',
  status: normalizeStatus(appointment.status),
  type: appointment.appointment_type || 'Follow-up',
  reason: appointment.reason || 'Follow-up visit',
  department: appointment.department || '',
  notes: appointment.notes || '',
})

const buildInitialFormState = (appointment = null) => ({
  appointment_date: appointment?.date || '',
  appointment_time: appointment?.time || '',
  appointment_type: appointment?.type || 'Follow-up',
  reason: appointment?.reason || '',
  department: appointment?.department || '',
  notes: appointment?.notes || '',
})

export const PatientAppointments = () => {
  const { currentUser } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [appointments, setAppointments] = useState([])
  const [formState, setFormState] = useState(buildInitialFormState())
  const [feedback, setFeedback] = useState({ tone: '', message: '' })

  const mode = searchParams.get('mode') || ''
  const selectedId = searchParams.get('appointment') || ''

  const selectedAppointment = useMemo(
    () => appointments.find((item) => item.id === selectedId) || null,
    [appointments, selectedId]
  )

  const fetchAppointments = useCallback(async () => {
    if (!currentUser?.id) {
      setLoading(false)
      return
    }

    setLoading(true)
    try {
      const response = await analyticsAPI.getAppointments()
      if (!response?.success) {
        throw new Error('Failed to fetch appointments')
      }

      const mapped = (response.data || [])
        .map(normalizeAppointment)
        .sort((left, right) => new Date(left.date).getTime() - new Date(right.date).getTime())

      setAppointments(mapped)
      setFeedback((previous) => (previous.tone === 'error' ? { tone: '', message: '' } : previous))
    } catch (error) {
      console.error('Error fetching appointments:', error)
      setFeedback({
        tone: 'error',
        message: getApiErrorMessage(
          error,
          'Unable to load your appointments right now.'
        ),
      })
    } finally {
      setLoading(false)
    }
  }, [currentUser?.id])

  useEffect(() => {
    fetchAppointments()
  }, [fetchAppointments])

  useLayoutEffect(() => {
    if (mode === 'new') {
      setFormState(buildInitialFormState())
      return
    }

    if (mode === 'reschedule' && selectedAppointment) {
      setFormState(buildInitialFormState(selectedAppointment))
    }
  }, [mode, selectedAppointment])

  const openWorkspace = (nextMode, appointmentId = '') => {
    const nextParams = new URLSearchParams()
    nextParams.set('mode', nextMode)
    if (appointmentId) nextParams.set('appointment', appointmentId)
    setSearchParams(nextParams)
    setFeedback({ tone: '', message: '' })
  }

  const closeWorkspace = () => {
    setSearchParams({})
    setFeedback({ tone: '', message: '' })
  }

  const handleFieldChange = (field) => (event) => {
    const value = event.target.value
    setFormState((previous) => ({ ...previous, [field]: value }))
  }

  const handleCancel = async (id) => {
    setSaving(true)
    try {
      const response = await analyticsAPI.updateAppointment(id, { status: 'Cancelled' })
      if (!response?.success) {
        throw new Error('Failed to cancel appointment')
      }

      await fetchAppointments()
      if (selectedId === id) closeWorkspace()
      setFeedback({ tone: 'success', message: 'Appointment cancelled successfully.' })
    } catch (error) {
      console.error('Failed to cancel appointment:', error)
      setFeedback({
        tone: 'error',
        message: getApiErrorMessage(
          error,
          'Unable to cancel this appointment.'
        ),
      })
    } finally {
      setSaving(false)
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setFeedback({ tone: '', message: '' })

    const payload = {
      appointment_date: formState.appointment_date,
      appointment_time: formState.appointment_time || null,
      appointment_type: formState.appointment_type,
      reason: formState.reason,
      department: formState.department || null,
      notes: formState.notes || null,
    }

    try {
      const response =
        mode === 'reschedule' && selectedAppointment
          ? await analyticsAPI.updateAppointment(selectedAppointment.id, payload)
          : await analyticsAPI.createAppointment(payload)

      if (!response?.success) {
        throw new Error(
          mode === 'reschedule'
            ? 'Failed to update appointment'
            : 'Failed to create appointment'
        )
      }

      await fetchAppointments()
      closeWorkspace()
      setFeedback({
        tone: 'success',
        message:
          mode === 'reschedule'
            ? 'Appointment updated successfully.'
            : 'Appointment request submitted successfully.',
      })
    } catch (error) {
      console.error('Failed to save appointment:', error)
      setFeedback({
        tone: 'error',
        message: getApiErrorMessage(
          error,
          'Unable to save appointment changes.'
        ),
      })
    } finally {
      setSaving(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'Scheduled':
        return '#2563eb'
      case 'Completed':
        return '#059669'
      case 'Cancelled':
        return '#dc2626'
      default:
        return '#64748b'
    }
  }

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <SkeletonText lines={1} width="250px" />
          <SkeletonText lines={1} width="450px" />
        </div>
        <div className={styles.appointmentList}>
          {[1, 2, 3].map((item) => (
            <div key={item} className={styles.aptCardSkeleton}>
              <Skeleton width="60px" height="60px" borderRadius="12px" />
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Skeleton width="200px" height="24px" />
                  <Skeleton width="80px" height="24px" borderRadius="20px" />
                </div>
                <SkeletonText lines={1} width="150px" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <motion.div
      className={styles.container}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Medical Consultations</h1>
          <p className={styles.subtitle}>
            Track, book, and update your follow-up consultations from one trusted route.
          </p>
        </div>
        <button
          type="button"
          className={styles.headerAction}
          onClick={() => openWorkspace('new')}
        >
          Book Follow-up
        </button>
      </div>

      {feedback.message ? (
        <div
          className={`${styles.feedbackBanner} ${
            feedback.tone === 'error' ? styles.feedbackError : styles.feedbackSuccess
          }`}
          role="status"
        >
          {feedback.message}
        </div>
      ) : null}

      <AnimatePresence initial={false}>
        {mode === 'new' || (mode === 'reschedule' && selectedAppointment) || (mode === 'summary' && selectedAppointment) ? (
          <motion.section
            key={`${mode}-${selectedId || 'new'}`}
            className={styles.workspaceCard}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
          >
            <div className={styles.workspaceHeader}>
              <div>
                <h2 className={styles.workspaceTitle}>
                  {mode === 'new'
                    ? 'Request a new follow-up'
                    : mode === 'reschedule'
                      ? 'Reschedule appointment'
                      : 'Appointment summary'}
                </h2>
                <p className={styles.workspaceSubtitle}>
                  {mode === 'summary'
                    ? 'Review the saved appointment details from the live backend record.'
                    : 'Changes on this form are saved to the scheduling API immediately.'}
                </p>
              </div>
              <button type="button" className={styles.workspaceClose} onClick={closeWorkspace}>
                Close
              </button>
            </div>

            {mode === 'summary' && selectedAppointment ? (
              <div className={styles.summaryGrid}>
                <div className={styles.summaryItem}>
                  <span>Date</span>
                  <strong>{selectedAppointment.date || 'Pending'}</strong>
                </div>
                <div className={styles.summaryItem}>
                  <span>Time</span>
                  <strong>{selectedAppointment.time || 'Time TBD'}</strong>
                </div>
                <div className={styles.summaryItem}>
                  <span>Status</span>
                  <strong>{selectedAppointment.status}</strong>
                </div>
                <div className={styles.summaryItem}>
                  <span>Type</span>
                  <strong>{selectedAppointment.type}</strong>
                </div>
                <div className={styles.summaryItem}>
                  <span>Doctor</span>
                  <strong>{selectedAppointment.doctor}</strong>
                </div>
                <div className={styles.summaryItem}>
                  <span>Department</span>
                  <strong>{selectedAppointment.department || selectedAppointment.specialty}</strong>
                </div>
                <div className={`${styles.summaryItem} ${styles.summaryWide}`}>
                  <span>Reason</span>
                  <strong>{selectedAppointment.reason}</strong>
                </div>
                <div className={`${styles.summaryItem} ${styles.summaryWide}`}>
                  <span>Notes</span>
                  <strong>{selectedAppointment.notes || 'No extra notes recorded for this appointment.'}</strong>
                </div>
              </div>
            ) : (
              <form className={styles.formGrid} onSubmit={handleSubmit}>
                <label className={styles.field}>
                  <span>Appointment date</span>
                  <input
                    type="date"
                    value={formState.appointment_date}
                    onChange={handleFieldChange('appointment_date')}
                    required
                  />
                </label>

                <label className={styles.field}>
                  <span>Appointment time</span>
                  <input
                    type="time"
                    value={formState.appointment_time}
                    onChange={handleFieldChange('appointment_time')}
                  />
                </label>

                <label className={styles.field}>
                  <span>Appointment type</span>
                  <input
                    type="text"
                    value={formState.appointment_type}
                    onChange={handleFieldChange('appointment_type')}
                    placeholder="Follow-up"
                    required
                  />
                </label>

                <label className={styles.field}>
                  <span>Department</span>
                  <input
                    type="text"
                    value={formState.department}
                    onChange={handleFieldChange('department')}
                    placeholder="Cardiology, Neurology, Imaging..."
                  />
                </label>

                <label className={`${styles.field} ${styles.fieldWide}`}>
                  <span>Reason</span>
                  <textarea
                    value={formState.reason}
                    onChange={handleFieldChange('reason')}
                    placeholder="Describe why this follow-up should be scheduled."
                    rows={3}
                    minLength={5}
                    maxLength={500}
                    required
                  />
                </label>

                <label className={`${styles.field} ${styles.fieldWide}`}>
                  <span>Notes</span>
                  <textarea
                    value={formState.notes}
                    onChange={handleFieldChange('notes')}
                    placeholder="Optional details for the care team."
                    rows={3}
                  />
                </label>

                <div className={styles.formActions}>
                  <button type="button" className={styles.secondaryAction} onClick={closeWorkspace}>
                    Cancel
                  </button>
                  <button type="submit" className={styles.primaryAction} disabled={saving}>
                    {saving
                      ? 'Saving...'
                      : mode === 'reschedule'
                        ? 'Save changes'
                        : 'Book appointment'}
                  </button>
                </div>
              </form>
            )}
          </motion.section>
        ) : null}
      </AnimatePresence>

      <div className={styles.appointmentList}>
        {appointments.map((appointment) => (
          <motion.div
            key={appointment.id}
            className={styles.aptCard}
            whileHover={{ x: 5, backgroundColor: '#fdfdfd' }}
          >
            <div className={styles.dateBox}>
              <span className={styles.day}>{new Date(appointment.date).getDate()}</span>
              <span className={styles.month}>
                {new Date(appointment.date).toLocaleString('default', { month: 'short' })}
              </span>
            </div>

            <div className={styles.info}>
              <div className={styles.aptHeader}>
                <h3 className={styles.doctorName}>{appointment.doctor}</h3>
                <span
                  className={styles.statusBadge}
                  style={{
                    backgroundColor: `${getStatusColor(appointment.status)}15`,
                    color: getStatusColor(appointment.status),
                  }}
                >
                  {appointment.status}
                </span>
              </div>

              <div className={styles.details}>
                <span className={styles.specialty}>{appointment.specialty}</span>
                <span className={styles.dot}>•</span>
                <span className={styles.type}>{appointment.type}</span>
                <span className={styles.dot}>•</span>
                <span className={styles.time}>{appointment.time || 'Time TBD'}</span>
              </div>
            </div>

            <div className={styles.actions}>
              <button
                type="button"
                className={styles.summaryBtn}
                onClick={() => openWorkspace('summary', appointment.id)}
              >
                View Summary
              </button>

              {appointment.status === 'Scheduled' ? (
                <>
                  <button
                    type="button"
                    className={styles.cancelBtn}
                    onClick={() => handleCancel(appointment.id)}
                    disabled={saving}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className={styles.rescheduleBtn}
                    onClick={() => openWorkspace('reschedule', appointment.id)}
                  >
                    Reschedule
                  </button>
                </>
              ) : null}
            </div>
          </motion.div>
        ))}
      </div>

      {appointments.length === 0 ? (
        <div className={styles.emptyState}>
          <span className={styles.emptyIcon}>AP</span>
          <h3>No Appointments Found</h3>
          <p>You do not have any scheduled follow-up visits yet.</p>
          <button
            type="button"
            className={styles.bookBtn}
            onClick={() => openWorkspace('new')}
          >
            Book New Appointment
          </button>
        </div>
      ) : null}
    </motion.div>
  )
}

export default PatientAppointments
