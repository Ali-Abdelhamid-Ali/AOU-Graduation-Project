import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { useGeography } from '../hooks/useGeography'
import { TopBar } from '../components/TopBar'
import { InputField } from '../components/InputField'
import { SelectField } from '../components/SelectField'
import SearchableSelect from '../components/SearchableSelect'
import { AnimatedButton } from '../components/AnimatedButton'
import { genderOptions, bloodTypeOptions } from '../constants/options'
import styles from './CreatePatient.module.css'

const CreatePatient = ({ onBack, userRole }) => {
    const { registerPatient, isLoading: authLoading } = useAuth()
    const {
        countries,
        regions,
        hospitals,
        selectCountry,
        selectRegion
    } = useGeography()

    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [success, setSuccess] = useState(null)
    const [showPassword, setShowPassword] = useState(false)

    const [formData, setFormData] = useState({
        email: '',
        password: '',
        firstName: '',
        lastName: '',
        firstNameAr: '', // [NEW] Arabic Name
        lastNameAr: '', // [NEW] Arabic Name
        dateOfBirth: '',
        gender: 'male',
        bloodType: 'unknown',

        // IDs
        nationalId: '', // [NEW]
        passportNumber: '', // [NEW]

        phone: '',
        address: '',
        city: '',
        countryId: '',
        regionId: '',
        hospitalId: '',

        // Medical & Insurance
        insuranceProvider: '', // [NEW]
        insuranceNumber: '', // [NEW]

        allergies: '',
        chronicConditions: '',

        // Emergency
        emergencyContactName: '',
        emergencyContactPhone: '',
        emergencyContactRelation: '',

        currentMedications: '',
        notes: ''
    })

    // Set default country (Egypt) once countries are loaded
    // Set default country (Egypt) once countries are loaded
    useEffect(() => {
        if (countries.length > 0 && !formData.countryId) {
            const egypt = countries.find(c => c.country_name === 'Egypt') || countries[0]
            if (egypt) {
                handleInputChange('countryId', egypt.country_id)
                selectCountry(egypt.country_id)
            }
        }
    }, [countries, formData.countryId, handleInputChange, selectCountry])

    const onCountryChange = (e) => {
        const val = e.target.value
        handleInputChange('countryId', val)
        handleInputChange('regionId', '')
        handleInputChange('hospitalId', '')
        selectCountry(val)
    }

    const onRegionChange = (e) => {
        const val = e.target.value
        handleInputChange('regionId', val)
        handleInputChange('hospitalId', '')
        selectRegion(val)
    }

    const validatePassword = (pass) => {
        if (pass.length < 6) return "Password must be at least 6 characters long."
        return null
    }

    const handleInputChange = useCallback((field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }))
        setError(null)
    }, [])

    const handleSubmit = async (e) => {
        e.preventDefault()

        const passwordError = validatePassword(formData.password)
        if (passwordError) {
            setError(passwordError)
            return
        }

        if (!formData.hospitalId) {
            setError("Hospital selection is required.")
            return
        }

        setLoading(true)
        setError(null)

        // Split lists by comma



        // Resolve IDs to Names
        const selectedCountry = countries.find(c => c.country_id === formData.countryId);
        const selectedRegion = regions.find(r => r.region_id === formData.regionId);

        const patientData = {
            ...formData,
            country: selectedCountry ? selectedCountry.country_name : formData.countryId,
            region: selectedRegion ? selectedRegion.region_name : formData.regionId,
            allergies: formData.allergies ? formData.allergies.split(',').map(s => s.trim()) : [],
            chronicConditions: formData.chronicConditions ? formData.chronicConditions.split(',').map(s => s.trim()) : [],
            currentMedications: formData.currentMedications ? formData.currentMedications.split(',').map(s => s.trim()) : []
        }

        const result = await registerPatient(patientData)

        if (result.success) {
            setSuccess({
                message: 'Patient enrolled successfully!',
                mrn: result.mrn
            })
            setFormData({
                email: '', password: '', firstName: '', lastName: '',
                firstNameAr: '', lastNameAr: '',
                dateOfBirth: '', gender: 'male', bloodType: 'unknown', phone: '',
                nationalId: '', passportNumber: '',
                address: '', city: '', countryId: formData.countryId,
                regionId: formData.regionId, hospitalId: formData.hospitalId,
                insuranceProvider: '', insuranceNumber: '',
                allergies: '', chronicConditions: '', emergencyContactName: '',
                emergencyContactPhone: '', emergencyContactRelation: '',
                currentMedications: '', notes: ''
            })
        } else {
            setError(result.error || 'Registration failed')
        }
        setLoading(false)
    }

    if (success) {
        return (
            <div className={styles.pageWrapper}>
                <TopBar userRole="admin" onBack={() => setSuccess(null)} />
                <div className={styles.container}>
                    <motion.div className={styles.card} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
                        <div className={styles.successView}>
                            <div className={styles.successIcon}>✅</div>
                            <h2 className={styles.title}>Patient Enrolled Successfully</h2>
                            <p className={styles.subtitle}>
                                Medical Record Number generated: <strong><span style={{ color: 'var(--color-primary)' }}>{success.mrn}</span></strong>
                            </p>
                            <div className={styles.successActions}>
                                <AnimatedButton variant="primary" fullWidth onClick={() => setSuccess(null)}>
                                    Enroll Another Patient
                                </AnimatedButton>
                                <AnimatedButton variant="secondary" fullWidth onClick={onBack}>
                                    Return to Dashboard
                                </AnimatedButton>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </div>
        )
    }

    return (
        <div className={styles.pageWrapper}>
            <TopBar userRole={userRole} onBack={onBack} />
            <div className={styles.container}>
                <motion.div className={styles.card} initial="hidden" animate="visible" variants={{
                    hidden: { opacity: 0, y: 20 },
                    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
                }}>
                    <div className={styles.header}>
                        <h1 className={styles.title}>Patient Enrollment</h1>
                        <p className={styles.subtitle}>Initialize a new patient record in the BioIntellect system.</p>
                    </div>

                    <AnimatePresence>
                        {error && (
                            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className={styles.alertError}>
                                {error}
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <form onSubmit={handleSubmit} className={styles.form}>
                        <section className={styles.section}>
                            <h3 className={styles.sectionTitle}>1. Account Information</h3>
                            <div className={`${styles.grid} ${styles.grid2}`}>
                                <InputField label="Email Address" type="email" value={formData.email} onChange={(e) => handleInputChange('email', e.target.value)} required />
                                <div className={styles.passwordWrapper}>
                                    <InputField
                                        label="Portal Password"
                                        type={showPassword ? "text" : "password"}
                                        value={formData.password}
                                        onChange={(e) => handleInputChange('password', e.target.value)}
                                        required
                                    />
                                    <button type="button" onClick={() => setShowPassword(!showPassword)} className={styles.togglePassword}>
                                        {showPassword ? "HIDE" : "SHOW"}
                                    </button>
                                </div>
                            </div>
                        </section>

                        <section className={styles.section}>
                            <h3 className={styles.sectionTitle}>2. Personal Profile</h3>
                            <div className={`${styles.grid} ${styles.grid3}`}>
                                <InputField label="First Name (English)" value={formData.firstName} onChange={(e) => handleInputChange('firstName', e.target.value)} required />
                                <InputField label="Last Name (English)" value={formData.lastName} onChange={(e) => handleInputChange('lastName', e.target.value)} required />
                                <InputField label="Birth Date" type="date" value={formData.dateOfBirth} onChange={(e) => handleInputChange('dateOfBirth', e.target.value)} required />

                                <InputField label="First Name (Arabic)" value={formData.firstNameAr} onChange={(e) => handleInputChange('firstNameAr', e.target.value)} placeholder="الاسم الأول - اختياري" />
                                <InputField label="Last Name (Arabic)" value={formData.lastNameAr} onChange={(e) => handleInputChange('lastNameAr', e.target.value)} placeholder="اسم العائلة - اختياري" />
                                <SelectField label="Gender" value={formData.gender} onChange={(e) => handleInputChange('gender', e.target.value)} options={genderOptions} required />

                                <InputField label="National ID / SSN" value={formData.nationalId} onChange={(e) => handleInputChange('nationalId', e.target.value)} placeholder="Optional" />
                                <InputField label="Passport Number" value={formData.passportNumber} onChange={(e) => handleInputChange('passportNumber', e.target.value)} placeholder="Optional" />
                                <InputField label="Phone Number" value={formData.phone} onChange={(e) => handleInputChange('phone', e.target.value)} />

                                <SelectField label="Blood Type" value={formData.bloodType} onChange={(e) => handleInputChange('bloodType', e.target.value)} options={bloodTypeOptions} />
                            </div>
                        </section>

                        <section className={styles.section}>
                            <h3 className={styles.sectionTitle}>3. Location & Facility</h3>
                            <div className={`${styles.grid} ${styles.grid3}`}>
                                <SearchableSelect
                                    label="Country"
                                    value={formData.countryId}
                                    onChange={onCountryChange}
                                    options={countries.map(c => ({ value: c.country_id, label: c.country_name, flag_url: c.flag_url }))}
                                    isCountry
                                    required
                                />
                                <SearchableSelect
                                    label="Region"
                                    value={formData.regionId}
                                    onChange={onRegionChange}
                                    options={regions.map(r => ({ value: r.region_id, label: r.region_name }))}
                                    disabled={!formData.countryId}
                                    required
                                />
                                <SearchableSelect
                                    label="Hospital"
                                    value={formData.hospitalId}
                                    onChange={(e) => handleInputChange('hospitalId', e.target.value)}
                                    options={hospitals.map(h => ({ value: h.hospital_id, label: h.hospital_name }))}
                                    disabled={!formData.regionId}
                                    required
                                />
                                <InputField label="City" value={formData.city} onChange={(e) => handleInputChange('city', e.target.value)} />
                                <InputField label="Full Address" value={formData.address} onChange={(e) => handleInputChange('address', e.target.value)} />
                            </div>
                        </section>

                        <section className={styles.section}>
                            <h3 className={styles.sectionTitle}>4. Insurance & Coverage</h3>
                            <div className={`${styles.grid} ${styles.grid2}`}>
                                <InputField label="Insurance Provider" value={formData.insuranceProvider} onChange={(e) => handleInputChange('insuranceProvider', e.target.value)} placeholder="e.g. AXA, MetLife" />
                                <InputField label="Policy / Member Number" value={formData.insuranceNumber} onChange={(e) => handleInputChange('insuranceNumber', e.target.value)} />
                            </div>
                        </section>

                        <section className={styles.section}>
                            <h3 className={styles.sectionTitle}>5. Emergency Contact</h3>
                            <div className={`${styles.grid} ${styles.grid3}`}>
                                <InputField label="Contact Name" value={formData.emergencyContactName} onChange={(e) => handleInputChange('emergencyContactName', e.target.value)} />
                                <InputField label="Contact Phone" value={formData.emergencyContactPhone} onChange={(e) => handleInputChange('emergencyContactPhone', e.target.value)} />
                                <InputField label="Relationship" value={formData.emergencyContactRelation} onChange={(e) => handleInputChange('emergencyContactRelation', e.target.value)} />
                            </div>
                        </section>

                        <section className={styles.section}>
                            <h3 className={styles.sectionTitle}>6. Clinical Summary</h3>
                            <div className={`${styles.grid} ${styles.grid2}`}>
                                <InputField label="Allergies (comma separated)" value={formData.allergies} onChange={(e) => handleInputChange('allergies', e.target.value)} />
                                <InputField label="Chronic Conditions (comma separated)" value={formData.chronicConditions} onChange={(e) => handleInputChange('chronicConditions', e.target.value)} />
                                <InputField label="Current Medications" value={formData.currentMedications} onChange={(e) => handleInputChange('currentMedications', e.target.value)} multiline />
                                <InputField label="Internal Notes" value={formData.notes} onChange={(e) => handleInputChange('notes', e.target.value)} multiline />
                            </div>
                        </section>

                        <AnimatedButton
                            type="submit"
                            variant="primary"
                            size="large"
                            fullWidth
                            isLoading={loading || authLoading}
                            className={styles.submitButton}
                        >
                            Enroll Patient
                        </AnimatedButton>
                    </form>
                </motion.div>
            </div>
        </div>
    )
}

export default CreatePatient
