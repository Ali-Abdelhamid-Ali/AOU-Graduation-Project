import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { supabase } from '../config/supabase'
import { Skeleton, SkeletonText, SkeletonCircle } from '../components/Skeleton'
import styles from './PatientAppointments.module.css'

export const PatientAppointments = () => {
    const { currentUser } = useAuth()
    const [loading, setLoading] = useState(true)
    const [appointments, setAppointments] = useState([])

    const fetchRealAppointments = async () => {
        if (!currentUser?.id) {
            setLoading(false);
            return;
        }
        setLoading(true)

        try {
            const { data, error } = await supabase
                .from('appointments')
                .select(`
                    id,
                    appointment_date,
                    appointment_time,
                    status,
                    appointment_type,
                    doctors (
                        first_name,
                        last_name
                    )
                `)
                .eq('patient_id', currentUser.id)
                .order('appointment_date', { ascending: false });

            if (error) throw error;

            const mapped = (data || []).map(apt => ({
                id: apt.id,
                doctor: apt.doctors ? `Dr. ${apt.doctors.first_name} ${apt.doctors.last_name}` : 'Clinical Staff',
                specialty: 'Medical Specialist',
                date: apt.appointment_date,
                time: apt.appointment_time,
                status: apt.status || 'Scheduled',
                type: apt.appointment_type || 'Consultation'
            }));

            setAppointments(mapped);
        } catch (error) {
            console.error('Error fetching real appointments:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRealAppointments();
    }, [currentUser])

    const handleCancel = async (id) => {
        try {
            const { error } = await supabase
                .from('appointments')
                .update({ status: 'Cancelled' })
                .eq('id', id);

            if (error) throw error;
            await fetchRealAppointments();
        } catch (error) {
            console.error('Failed to cancel appointment:', error);
        }
    }

    const getStatusColor = (status) => {
        switch (status) {
            case 'Scheduled': return '#3b82f6';
            case 'Completed': return '#10b981';
            case 'Cancelled': return '#ef4444';
            default: return '#64748b';
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
                    {[1, 2, 3].map(i => (
                        <div key={i} className={styles.aptCardSkeleton}>
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
                <h1 className={styles.title}>Medical Consultations</h1>
                <p className={styles.subtitle}>Track and manage your upcoming and past clinical visits.</p>
            </div>

            <div className={styles.appointmentList}>
                {appointments.map((apt) => (
                    <motion.div
                        key={apt.id}
                        className={styles.aptCard}
                        whileHover={{ x: 5, backgroundColor: '#fdfdfd' }}
                    >
                        <div className={styles.dateBox}>
                            <span className={styles.day}>{new Date(apt.date).getDate()}</span>
                            <span className={styles.month}>{new Date(apt.date).toLocaleString('default', { month: 'short' })}</span>
                        </div>
                        <div className={styles.info}>
                            <div className={styles.aptHeader}>
                                <h3 className={styles.doctorName}>{apt.doctor}</h3>
                                <span
                                    className={styles.statusBadge}
                                    style={{ backgroundColor: `${getStatusColor(apt.status)}15`, color: getStatusColor(apt.status) }}
                                >
                                    {apt.status}
                                </span>
                            </div>
                            <div className={styles.details}>
                                <span className={styles.specialty}>{apt.specialty}</span>
                                <span className={styles.dot}>•</span>
                                <span className={styles.type}>{apt.type}</span>
                                <span className={styles.dot}>•</span>
                                <span className={styles.time}>{apt.time}</span>
                            </div>
                        </div>
                        <div className={styles.actions}>
                            {apt.status === 'Scheduled' ? (
                                <>
                                    <button
                                        className={styles.cancelBtn}
                                        onClick={() => handleCancel(apt.id)}
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        className={styles.rescheduleBtn}
                                        onClick={() => alert('Rescheduling request sent to medical coordinator.')}
                                    >
                                        Reschedule
                                    </button>
                                </>
                            ) : (
                                <button
                                    className={styles.summaryBtn}
                                    onClick={() => alert('Downloading clinical summary...')}
                                >
                                    View Summary
                                </button>
                            )}
                        </div>
                    </motion.div>
                ))}
            </div>

            {appointments.length === 0 && (
                <div className={styles.emptyState}>
                    <span className={styles.emptyIcon}>📅</span>
                    <h3>No Appointments Found</h3>
                    <p>You haven't scheduled any medical consultations yet.</p>
                    <button
                        className={styles.bookBtn}
                        onClick={() => alert('Booking system is currently syncing with hospital calendar.')}
                    >
                        Book New Appointment
                    </button>
                </div>
            )}
        </motion.div>
    )
}
