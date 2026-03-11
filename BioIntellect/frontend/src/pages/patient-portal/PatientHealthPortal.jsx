import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/store/AuthContext'
import { useGeography } from '@/hooks/useGeography'
import { InputField } from '@/components/ui/InputField'
import { SelectField } from '@/components/ui/SelectField'
import SearchableSelect from '@/components/ui/SearchableSelect'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import { genderOptions, bloodTypeOptions } from '@/config/options'
import {
    formatListForInput,
    formatMedicationListForInput
} from '@/utils/userFormUtils'
import styles from './PatientHealthPortal.module.css'

export const PatientHealthPortal = () => {
    const { currentUser, updatePatientProfile, isLoading: authLoading } = useAuth()
    const { countries, regions, selectCountry, selectRegion } = useGeography()

    const [activeTab, setActiveTab] = useState('identity')
    const [saving, setSaving] = useState(false)
    const [message, setMessage] = useState({ type: '', text: '' })

    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        first_name_ar: '',
        last_name_ar: '',
        date_of_birth: '',
        gender: '',
        blood_type: '',
        phone: '',
        national_id: '',
        passport_number: '',
        address: '',
        city: '',
        country_id: '',
        region_id: '',
        insurance_provider: '',
        insurance_number: '',
        emergency_contact_name: '',
        emergency_contact_phone: '',
        emergency_contact_relation: '',
        allergies: '',
        chronic_conditions: '',
        current_medications: '',
        notes: ''
    })

    useEffect(() => {
        if (currentUser) {
            setFormData({
                first_name: currentUser.first_name || '',
                last_name: currentUser.last_name || '',
                first_name_ar: currentUser.first_name_ar || '',
                last_name_ar: currentUser.last_name_ar || '',
                date_of_birth: currentUser.date_of_birth || '',
                gender: currentUser.gender || 'male',
                blood_type: currentUser.blood_type || 'unknown',
                phone: currentUser.phone || '',
                national_id: currentUser.national_id || '',
                passport_number: currentUser.passport_number || '',
                address: currentUser.address || '',
                city: currentUser.city || '',
                country_id: currentUser.country_id || '',
                region_id: currentUser.region_id || '',
                insurance_provider: currentUser.insurance_provider || '',
                insurance_number: currentUser.insurance_number || '',
                emergency_contact_name: currentUser.emergency_contact_name || '',
                emergency_contact_phone: currentUser.emergency_contact_phone || '',
                emergency_contact_relation: currentUser.emergency_contact_relation || '',
                allergies: formatListForInput(currentUser.allergies),
                chronic_conditions: formatListForInput(currentUser.chronic_conditions),
                current_medications: formatMedicationListForInput(currentUser.current_medications),
                notes: currentUser.notes || ''
            })

            if (currentUser.country_id) selectCountry(currentUser.country_id)
            if (currentUser.region_id) selectRegion(currentUser.region_id)
        }
    }, [currentUser, selectCountry, selectRegion])

    const handleSave = async (e) => {
        e.preventDefault()
        setSaving(true)
        setMessage({ type: '', text: '' })

        const result = await updatePatientProfile(formData)

        if (result.success) {
            setMessage({ type: 'success', text: 'Clinical Health Record updated successfully.' })
        } else {
            setMessage({ type: 'error', text: result.error || 'Failed to update record.' })
        }
        setSaving(false)
        setTimeout(() => setMessage({ type: '', text: '' }), 5000)
    }

    const tabs = [
        { id: 'identity', label: 'Identity', icon: '👤' },
        { id: 'medical', label: 'Clinical History', icon: '🏥' },
        { id: 'safety', label: 'Insurance & Safety', icon: '🛡️' },
        { id: 'location', label: 'Contact & Location', icon: '📍' }
    ]

    return (
        <div className={styles.portalWrapper}>
            <header className={styles.portalHeader}>
                <div className={styles.headerTitleGroup}>
                    <h1 className={styles.title}>Patient Health Identity</h1>
                    <p className={styles.subtitle}>Unified clinical management and medical record control.</p>
                </div>
                <div className={styles.mrnBadge}>
                    <span className={styles.mrnLabel}>Clinical MRN</span>
                    <span className={styles.mrnValue}>{currentUser?.mrn || 'GEN-PENDING'}</span>
                </div>
            </header>

            <nav className={styles.tabNav}>
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        className={`${styles.tabBtn} ${activeTab === tab.id ? styles.active : ''}`}
                        onClick={() => setActiveTab(tab.id)}
                    >
                        <span className={styles.tabIcon}>{tab.icon}</span>
                        {tab.label}
                    </button>
                ))}
            </nav>

            <motion.div
                className={styles.portalContent}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <form onSubmit={handleSave} className={styles.portalForm}>
                    <AnimatePresence mode="wait">
                        {activeTab === 'identity' && (
                            <motion.section
                                key="identity"
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 10 }}
                                className={styles.section}
                            >
                                <h3 className={styles.sectionTitle}>Digital & Personal Identity</h3>
                                <div className={styles.formGrid}>
                                    <InputField
                                        label="First Name (English)"
                                        value={formData.first_name}
                                        onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                                        required
                                    />
                                    <InputField
                                        label="Last Name (English)"
                                        value={formData.last_name}
                                        onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                                        required
                                    />
                                    <InputField
                                        label="First Name (Arabic)"
                                        value={formData.first_name_ar}
                                        onChange={(e) => setFormData({ ...formData, first_name_ar: e.target.value })}
                                        placeholder="الاسم الأول"
                                    />
                                    <InputField
                                        label="Last Name (Arabic)"
                                        value={formData.last_name_ar}
                                        onChange={(e) => setFormData({ ...formData, last_name_ar: e.target.value })}
                                        placeholder="اسم العائلة"
                                    />
                                    <InputField
                                        label="Date of Birth"
                                        type="date"
                                        value={formData.date_of_birth}
                                        onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                                        required
                                    />
                                    <SelectField
                                        label="Gender"
                                        value={formData.gender}
                                        onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                                        options={genderOptions}
                                        required
                                    />
                                </div>
                                <div className={styles.formGrid}>
                                    <InputField
                                        label="National ID / SSN"
                                        value={formData.national_id}
                                        onChange={(e) => setFormData({ ...formData, national_id: e.target.value })}
                                    />
                                    <InputField
                                        label="Passport Number"
                                        value={formData.passport_number}
                                        onChange={(e) => setFormData({ ...formData, passport_number: e.target.value })}
                                    />
                                </div>
                            </motion.section>
                        )}

                        {activeTab === 'medical' && (
                            <motion.section
                                key="medical"
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 10 }}
                                className={styles.section}
                            >
                                <h3 className={styles.sectionTitle}>Clinical & Medical Profile</h3>
                                <div className={styles.formGrid}>
                                    <SelectField
                                        label="Blood Type"
                                        value={formData.blood_type}
                                        onChange={(e) => setFormData({ ...formData, blood_type: e.target.value })}
                                        options={bloodTypeOptions}
                                    />
                                    <InputField
                                        label="Active Allergies (comma separated)"
                                        value={formData.allergies}
                                        onChange={(e) => setFormData({ ...formData, allergies: e.target.value })}
                                        placeholder="e.g. Penicillin, Peanuts"
                                    />
                                </div>
                                <InputField
                                    label="Chronic Conditions (comma separated)"
                                    value={formData.chronic_conditions}
                                    onChange={(e) => setFormData({ ...formData, chronic_conditions: e.target.value })}
                                    placeholder="e.g. Diabetes Type 2, Hypertension"
                                    multiline
                                />
                                <InputField
                                    label="Current Medications"
                                    value={formData.current_medications}
                                    onChange={(e) => setFormData({ ...formData, current_medications: e.target.value })}
                                    multiline
                                />
                                <InputField
                                    label="Internal Profile Notes"
                                    value={formData.notes}
                                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                                    multiline
                                />
                            </motion.section>
                        )}

                        {activeTab === 'safety' && (
                            <motion.section
                                key="safety"
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 10 }}
                                className={styles.section}
                            >
                                <h3 className={styles.sectionTitle}>Security & Coverage</h3>
                                <div className={styles.formGrid}>
                                    <InputField
                                        label="Insurance Provider"
                                        value={formData.insurance_provider}
                                        onChange={(e) => setFormData({ ...formData, insurance_provider: e.target.value })}
                                    />
                                    <InputField
                                        label="Policy / Member ID"
                                        value={formData.insurance_number}
                                        onChange={(e) => setFormData({ ...formData, insurance_number: e.target.value })}
                                    />
                                </div>
                                <h4 className={styles.subSectionTitle}>Emergency Contact</h4>
                                <div className={styles.formGrid}>
                                    <InputField
                                        label="Contact Name"
                                        value={formData.emergency_contact_name}
                                        onChange={(e) => setFormData({ ...formData, emergency_contact_name: e.target.value })}
                                    />
                                    <InputField
                                        label="Contact Relationship"
                                        value={formData.emergency_contact_relation}
                                        onChange={(e) => setFormData({ ...formData, emergency_contact_relation: e.target.value })}
                                    />
                                    <InputField
                                        label="Emergency Phone"
                                        value={formData.emergency_contact_phone}
                                        onChange={(e) => setFormData({ ...formData, emergency_contact_phone: e.target.value })}
                                    />
                                </div>
                            </motion.section>
                        )}

                        {activeTab === 'location' && (
                            <motion.section
                                key="location"
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 10 }}
                                className={styles.section}
                            >
                                <h3 className={styles.sectionTitle}>Physical Location & Connectivity</h3>
                                <div className={styles.formGrid}>
                                    <InputField
                                        label="Primary Phone"
                                        value={formData.phone}
                                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                    />
                                    <InputField
                                        label="City"
                                        value={formData.city}
                                        onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                                    />
                                </div>
                                <div className={styles.formGrid}>
                                    <SearchableSelect
                                        label="Country"
                                        value={formData.country_id}
                                        onChange={(e) => {
                                            const val = e.target.value;
                                            setFormData({ ...formData, country_id: val, region_id: '' });
                                            selectCountry(val);
                                        }}
                                        options={countries.map(c => ({ value: c.country_id, label: c.country_name }))}
                                        required
                                    />
                                    <SearchableSelect
                                        label="Region / State"
                                        value={formData.region_id}
                                        onChange={(e) => {
                                            const val = e.target.value;
                                            setFormData({ ...formData, region_id: val });
                                            selectRegion(val);
                                        }}
                                        options={regions.map(r => ({ value: r.region_id, label: r.region_name }))}
                                        disabled={!formData.country_id}
                                        required
                                    />
                                </div>
                                <InputField
                                    label="Full Residential Address"
                                    value={formData.address}
                                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                                    multiline
                                />
                            </motion.section>
                        )}
                    </AnimatePresence>

                    <footer className={styles.portalFooter}>
                        {message.text && (
                            <motion.div
                                initial={{ opacity: 0, y: 5 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`${styles.statusMessage} ${styles[message.type]}`}
                            >
                                {message.type === 'success' ? '✅' : '❌'} {message.text}
                            </motion.div>
                        )}
                        <AnimatedButton
                            variant="primary"
                            type="submit"
                            isLoading={saving || authLoading}
                            className={styles.submitBtn}
                        >
                            Commit Clinical Changes
                        </AnimatedButton>
                    </footer>
                </form>
            </motion.div>
        </div>
    )
}
