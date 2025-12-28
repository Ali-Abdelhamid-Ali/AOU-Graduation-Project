import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { supabase } from '../config/supabase'
import { Skeleton, SkeletonText, SkeletonCircle } from '../components/Skeleton'
import { InputField } from '../components/InputField'
import { SelectField } from '../components/SelectField'
import { AnimatedButton } from '../components/AnimatedButton'
import styles from './PatientProfile.module.css'

export const PatientProfile = () => {
    const { currentUser, refreshUser } = useAuth()
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState({ type: '', text: '' })
    const fileInputRef = useRef(null)
    const [photoPreview, setPhotoPreview] = useState(null)

    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        date_of_birth: '',
        gender: '',
        phone: '',
        address: '',
    })

    useEffect(() => {
        if (currentUser) {
            setFormData({
                first_name: currentUser.first_name || '',
                last_name: currentUser.last_name || '',
                date_of_birth: currentUser.date_of_birth || '',
                gender: currentUser.gender || '',
                phone: currentUser.phone || '',
                address: currentUser.address || '',
            })
            setPhotoPreview(currentUser.photo_url || null)
            setLoading(false)
        } else {
            // Keep it loading for a bit until Auth might be done
            const checkAuth = setTimeout(() => setLoading(false), 2000);
            return () => clearTimeout(checkAuth);
        }
    }, [currentUser])

    const handlePhotoChange = async (e) => {
        const file = e.target.files[0]
        if (file) {
            // Visual preview
            const reader = new FileReader()
            reader.onloadend = () => setPhotoPreview(reader.result)
            reader.readAsDataURL(file)

            // Direct upload for real functionality
            await uploadPhoto(file)
        }
    }

    const uploadPhoto = async (file) => {
        setSaving(true)
        if (!currentUser?.id) {
            setSaving(false)
            setMessage({ type: 'error', text: 'User session not active.' })
            return
        }

        try {
            const fileExt = file.name.split('.').pop()
            const fileName = `avatar_${currentUser.id}_${Date.now()}.${fileExt}`
            const filePath = `avatars/${currentUser.id}/${fileName}`

            const { error: uploadError } = await supabase.storage
                .from('medical-files')
                .upload(filePath, file)

            if (uploadError) throw uploadError

            const { data: { publicUrl } } = supabase.storage
                .from('medical-files')
                .getPublicUrl(filePath)

            // Update patient record immediately
            const { error: updateError } = await supabase
                .from('patients')
                .update({ photo_url: publicUrl })
                .eq('id', currentUser?.id)

            if (updateError) throw updateError

            await refreshUser()
            setMessage({ type: 'success', text: 'Identity photo updated.' })
        } catch (error) {
            console.error('Photo upload failed:', error)
            setMessage({ type: 'error', text: 'Photo upload failed.' })
        } finally {
            setSaving(false)
        }
    }

    const handleSave = async (e) => {
        e.preventDefault()

        if (!currentUser?.id) {
            setMessage({ type: 'error', text: 'User session not active.' })
            return
        }

        setSaving(true)
        setMessage({ type: '', text: '' })

        try {
            // Upload photo if changed (Logic for Supabase storage would go here)
            // For now, updating clinical data in 'patients' table
            const { error } = await supabase
                .from('patients')
                .update({
                    first_name: formData.first_name,
                    last_name: formData.last_name,
                    date_of_birth: formData.date_of_birth,
                    gender: formData.gender,
                    phone: formData.phone,
                    address: formData.address,
                })
                .eq('id', currentUser?.id)

            if (error) throw error

            await refreshUser()
            setMessage({ type: 'success', text: 'Profile updated successfully!' })
        } catch (error) {
            setMessage({ type: 'error', text: error.message })
        } finally {
            setSaving(false)
            setTimeout(() => setMessage({ type: '', text: '' }), 3000)
        }
    }

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.header}>
                    <SkeletonText lines={1} width="300px" />
                    <SkeletonText lines={1} width="500px" />
                </div>
                <div className={styles.profileGrid}>
                    <div className={styles.photoCardSkeleton}>
                        <SkeletonCircle size="160px" />
                        <Skeleton width="120px" height="32px" borderRadius="12px" style={{ margin: '20px auto' }} />
                        <Skeleton width="100%" height="40px" borderRadius="12px" />
                    </div>
                    <div className={styles.formCardSkeleton}>
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} style={{ marginBottom: '20px' }}>
                                <SkeletonText lines={1} width="100px" />
                                <Skeleton width="100%" height="45px" borderRadius="12px" style={{ marginTop: '8px' }} />
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        )
    }

    return (
        <motion.div
            className={styles.container}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
        >
            <div className={styles.header}>
                <h1 className={styles.title}>Personal Health Identity</h1>
                <p className={styles.subtitle}>Manage your clinical information and digital presence.</p>
            </div>

            <div className={styles.profileGrid}>
                <div className={styles.photoCard}>
                    <div className={styles.photoContainer}>
                        <img
                            src={photoPreview || 'https://via.placeholder.com/150'}
                            alt="Profile"
                            className={styles.profileImage}
                        />
                        <button
                            className={styles.uploadBtn}
                            onClick={() => fileInputRef.current.click()}
                        >
                            📸 Change Photo
                        </button>
                        <input
                            type="file"
                            ref={fileInputRef}
                            style={{ display: 'none' }}
                            onChange={handlePhotoChange}
                            accept="image/*"
                        />
                    </div>
                    <div className={styles.idBadge}>
                        <span className={styles.mrnLabel}>MRN:</span>
                        <span className={styles.mrnValue}>{currentUser?.mrn || 'N/A'}</span>
                    </div>
                </div>

                <div className={styles.formCard}>
                    <form onSubmit={handleSave} className={styles.form}>
                        <div className={styles.row}>
                            <InputField
                                id="firstName"
                                label="First Name"
                                value={formData.first_name}
                                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                                required
                            />
                            <InputField
                                id="lastName"
                                label="Last Name"
                                value={formData.last_name}
                                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                                required
                            />
                        </div>

                        <InputField
                            id="dob"
                            label="Date of Birth"
                            type="date"
                            value={formData.date_of_birth}
                            onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                            required
                        />

                        <SelectField
                            id="gender"
                            label="Gender"
                            value={formData.gender}
                            onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                            options={[
                                { value: 'male', label: 'Male' },
                                { value: 'female', label: 'Female' },
                                { value: 'other', label: 'Other' }
                            ]}
                            required
                        />

                        <InputField
                            id="phone"
                            label="Phone Number"
                            value={formData.phone}
                            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        />

                        <InputField
                            id="address"
                            label="Primary Address"
                            value={formData.address}
                            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                        />

                        {message.text && (
                            <div className={`${styles.message} ${styles[message.type]}`}>
                                {message.text}
                            </div>
                        )}

                        <div className={styles.actions}>
                            <AnimatedButton
                                type="submit"
                                variant="primary"
                                isLoading={saving}
                                fullWidth
                            >
                                Save Clinical Record
                            </AnimatedButton>
                        </div>
                    </form>
                </div>
            </div>
        </motion.div>
    )
}
