import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { TopBar } from '../components/TopBar'
import { InputField } from '../components/InputField'
import { SelectField } from '../components/SelectField'
import { AnimatedButton } from '../components/AnimatedButton'
import { supabase } from '../config/supabase'
import styles from './SignUp.module.css' // Reusing styles for consistency

export const PatientDashboard = ({ onLogout }) => {
    const { currentUser, userRole, signOut } = useAuth()
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(false)
    const [profile, setProfile] = useState(null)
    const [editMode, setEditMode] = useState(false)
    const [message, setMessage] = useState({ type: '', text: '' })

    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        date_of_birth: '',
        gender: '',
        phone_number: '',
        address: '',
        medical_history: '',
    })

    useEffect(() => {
        fetchProfile()
    }, [currentUser])

    const fetchProfile = async () => {
        try {
            setLoading(true)

            // We need to fetch from the 'patients' table
            // The Link is via email or we can search by created user_id if we stored it properly in users table too
            // But based on logic, we have email in currentUser

            const { data, error } = await supabase
                .from('patients')
                .select('*')
                .eq('email', currentUser.email)
                .single()

            if (error) throw error

            setProfile(data)
            setFormData({
                first_name: data.first_name || '',
                last_name: data.last_name || '',
                date_of_birth: data.date_of_birth || '',
                gender: data.gender || '',
                phone_number: data.phone_number || '',
                address: data.address || '',
                medical_history: data.medical_history || '',
            })
        } catch (error) {
            console.error('Error loading patient data:', error.message)
            setMessage({ type: 'error', text: 'Failed to load profile data.' })
        } finally {
            setLoading(false)
        }
    }

    const handleUpdate = async (e) => {
        e.preventDefault()
        try {
            setUploading(true)
            const { error } = await supabase
                .from('patients')
                .update({
                    // Allowed fields to update
                    phone_number: formData.phone_number,
                    address: formData.address,
                    // gender/dob usually fixed but allow if needed or restriction logic applied here
                    gender: formData.gender,
                    date_of_birth: formData.date_of_birth,
                    first_name: formData.first_name,
                    last_name: formData.last_name
                })
                .eq('patient_id', profile.patient_id)

            if (error) throw error

            setMessage({ type: 'success', text: 'Profile updated successfully!' })
            setEditMode(false)
            fetchProfile()
        } catch (error) {
            setMessage({ type: 'error', text: error.message })
        } finally {
            setUploading(false)
        }
    }

    const handleLogout = async () => {
        await signOut()
        if (onLogout) onLogout()
    }

    if (loading) {
        return (
            <div className={styles.pageWrapper} style={{ justifyContent: 'center', alignItems: 'center' }}>
                <p style={{ color: 'white' }}>Loading profile...</p>
            </div>
        )
    }

    return (
        <div className={styles.pageWrapper}>
            {/* Simple Top Bar for Dashboard */}
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, padding: '1rem', display: 'flex', justifyContent: 'space-between', zIndex: 10 }}>
                <h2 style={{ color: 'white', margin: 0 }}>BioIntellect Patient Portal</h2>
                <button
                    onClick={handleLogout}
                    style={{
                        background: 'rgba(255,255,255,0.1)',
                        border: '1px solid rgba(255,255,255,0.2)',
                        padding: '8px 16px',
                        borderRadius: '8px',
                        color: 'white',
                        cursor: 'pointer'
                    }}
                >
                    Sign Out
                </button>
            </div>

            <div className={styles.container} style={{ marginTop: '60px' }}>
                <motion.div
                    className={styles.card}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    style={{ maxWidth: '800px', width: '100%' }}
                >
                    <div className={styles.header}>
                        <h1 className={styles.title}>My Health Profile</h1>
                        <p className={styles.subtitle}>
                            MRN: <span style={{ fontFamily: 'monospace', background: 'rgba(0,0,0,0.1)', padding: '2px 6px', borderRadius: '4px' }}>{profile?.medical_record_number}</span>
                        </p>
                    </div>

                    {message.text && (
                        <div className={message.type === 'error' ? styles.alertError : styles.alertSuccess} style={{ color: message.type === 'success' ? '#10b981' : '#ef4444', background: message.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', padding: '10px', borderRadius: '8px', marginBottom: '1rem', textAlign: 'center' }}>
                            {message.text}
                        </div>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
                        {!editMode && (
                            <button
                                onClick={() => setEditMode(true)}
                                style={{ background: 'none', border: 'none', color: 'var(--color-primary)', cursor: 'pointer', fontWeight: 600 }}
                            >
                                Edit Profile
                            </button>
                        )}
                        {editMode && (
                            <button
                                onClick={() => { setEditMode(false); fetchProfile(); }}
                                style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', marginRight: '1rem' }}
                            >
                                Cancel
                            </button>
                        )}
                    </div>

                    <form onSubmit={handleUpdate} className={styles.form}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            {/* Personal Info */}
                            <InputField
                                id="first_name"
                                label="First Name"
                                value={formData.first_name}
                                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                                disabled={!editMode}
                            />
                            <InputField
                                id="last_name"
                                label="Last Name"
                                value={formData.last_name}
                                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                                disabled={!editMode}
                            />

                            <InputField
                                id="dob"
                                label="Date of Birth"
                                type="date"
                                value={formData.date_of_birth}
                                onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                                disabled={!editMode}
                            />
                            <SelectField
                                id="gender"
                                label="Gender"
                                value={formData.gender}
                                onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                                options={[
                                    { value: 'male', label: 'Male' },
                                    { value: 'female', label: 'Female' },
                                ]}
                                disabled={!editMode}
                            />

                            <InputField
                                id="phone"
                                label="Phone Number"
                                value={formData.phone_number}
                                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                                disabled={!editMode}
                                placeholder="+1 234 567 8900"
                            />
                            <InputField
                                id="address"
                                label="Address"
                                value={formData.address}
                                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                                disabled={!editMode}
                                placeholder="123 Health St"
                            />
                        </div>

                        {/* Read Only Stats or Info */}
                        <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                            <h3 style={{ fontSize: '1rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>Account Info</h3>
                            <p style={{ margin: 0 }}>Email: {currentUser?.email}</p>
                            <p style={{ margin: 0 }}>Role: {userRole}</p>
                        </div>

                        {editMode && (
                            <AnimatedButton
                                type="submit"
                                variant="primary"
                                size="large"
                                fullWidth
                                isLoading={uploading}
                            >
                                Save Changes
                            </AnimatedButton>
                        )}
                    </form>
                </motion.div>
            </div>
        </div>
    )
}
