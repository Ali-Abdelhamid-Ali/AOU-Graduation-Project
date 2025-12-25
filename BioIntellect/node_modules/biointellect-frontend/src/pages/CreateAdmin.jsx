import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { useGeography } from '../hooks/useGeography'
import { TopBar } from '../components/TopBar'
import { InputField } from '../components/InputField'
import { SelectField } from '../components/SelectField'
import SearchableSelect from '../components/SearchableSelect'
import { AnimatedButton } from '../components/AnimatedButton'
import styles from './CreateDoctor.module.css' // Reusing styles for consistency

import { adminOptions } from '../constants/options'


export const CreateAdmin = ({ onBack, userRole }) => {
    const { registerAdmin, isLoading, error, clearError } = useAuth()
    const {
        countries,
        regions,
        hospitals,
        selectCountry,
        selectRegion
    } = useGeography()

    const [formData, setFormData] = useState({
        fullName: '',
        email: '',
        role: '',
        password: '',
        confirmPassword: '',
        countryId: '',
        countryCode: '',
        countryName: '',
        regionId: '',
        regionName: '',
        hospitalId: ''
    })

    const [validationErrors, setValidationErrors] = useState({})
    const [success, setSuccess] = useState(false)

    // Set default country (Egypt) once countries are loaded
    useEffect(() => {
        if (countries.length > 0 && !formData.countryId) {
            const defaultCountry = countries.find(c => c.country_name === 'Egypt') || countries[0]
            handleInputChange('countryId', defaultCountry.country_id)
            handleInputChange('countryCode', defaultCountry.country_code)
            handleInputChange('countryName', defaultCountry.country_name)
            selectCountry(defaultCountry.country_id)
        }
    }, [countries])

    const onCountryChange = (e) => {
        const selected = countries.find(c => c.country_id === e.target.value)
        handleInputChange('countryId', e.target.value)
        handleInputChange('countryCode', selected?.country_code || '')
        handleInputChange('countryName', selected?.country_name || '')
        selectCountry(e.target.value)
    }

    const onRegionChange = (e) => {
        const selected = regions.find(r => r.region_id === e.target.value)
        handleInputChange('regionId', e.target.value)
        handleInputChange('regionName', selected?.region_name || '')
        selectRegion(e.target.value)
    }

    const handleInputChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }))
        if (validationErrors[field]) {
            setValidationErrors(prev => ({ ...prev, [field]: '' }))
        }
        clearError()
    }

    const validateForm = () => {
        const errors = {}
        if (!formData.fullName.trim()) errors.fullName = 'System name is required'
        if (!formData.email.trim()) errors.email = 'Administrative email is required'
        if (!formData.role) errors.role = 'System Role is required'
        if (!formData.hospitalId) errors.hospitalId = 'Assigned hospital is required'

        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]).{16,}$/
        if (!formData.password) {
            errors.password = 'Password is required'
        } else if (!passwordRegex.test(formData.password)) {
            errors.password = 'Password must be 16+ chars with mixed cases, digits & symbols'
        }

        if (formData.password !== formData.confirmPassword) {
            errors.confirmPassword = 'Passwords do not match'
        }

        setValidationErrors(errors)
        return Object.keys(errors).length === 0
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!validateForm()) return

        const result = await registerAdmin(formData)
        if (result.success) {
            setSuccess(true)
        }
    }

    if (success) {
        return (
            <div className={styles.pageWrapper}>
                <TopBar userRole="administrator" onBack={() => {
                    setSuccess(false); setFormData({
                        fullName: '', email: '', role: '', password: '', confirmPassword: '',
                        countryId: '', countryCode: '', countryName: '', regionId: '', regionName: '', hospitalId: ''
                    })
                }} />
                <div className={styles.container}>
                    <motion.div
                        className={styles.card}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                    >
                        <div className={styles.successView}>
                            <div className={styles.successIcon}>🔑</div>
                            <h2 className={styles.title}>Admin Access Granted</h2>
                            <p className={styles.subtitle}>
                                <strong>{formData.fullName}</strong> has been provisioned as an {formData.role === 'administrator' ? 'Administrator' : 'Mini Administrator'}.
                                <br /><br />
                                <span style={{ color: 'var(--color-primary)', fontWeight: '600' }}>
                                    ⚠️ IMPORTANT: The new administrator must confirm their email address before their system credentials become active.
                                </span>
                            </p>
                            <div className={styles.successActions}>
                                <AnimatedButton variant="primary" fullWidth onClick={() => {
                                    setSuccess(false); setFormData({
                                        fullName: '', email: '', role: '', password: '', confirmPassword: '',
                                        countryId: '', countryCode: '', countryName: '', regionId: '', regionName: '', hospitalId: ''
                                    })
                                }}>Provision Another Administrator</AnimatedButton>
                                <AnimatedButton variant="secondary" fullWidth onClick={onBack}>Back to Command Center</AnimatedButton>
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
                <motion.div
                    className={styles.card}
                    initial="hidden"
                    animate="visible"
                    variants={{
                        hidden: { opacity: 0, scale: 0.98 },
                        visible: {
                            opacity: 1,
                            scale: 1,
                            transition: {
                                duration: 0.8,
                                ease: [0.22, 1, 0.36, 1],
                                staggerChildren: 0.15
                            }
                        }
                    }}
                >
                    <div className={styles.header}>
                        <h1 className={styles.title}>Provision Secondary Administrator</h1>
                        <p className={styles.subtitle}>Grant full administrative access to the clinical management infrastructure of BioIntellect.</p>
                    </div>

                    {error && <div className={styles.alertError}>{error}</div>}

                    <form onSubmit={handleSubmit} className={styles.form}>
                        <div className={styles.grid}>
                            <InputField
                                label="Administrator Full Name"
                                placeholder="E.g. Engineering Lead"
                                value={formData.fullName}
                                onChange={(e) => handleInputChange('fullName', e.target.value)}
                                error={validationErrors.fullName}
                                required
                            />
                            <InputField
                                label="System Email"
                                type="email"
                                placeholder="admin@biointellect.com"
                                value={formData.email}
                                onChange={(e) => handleInputChange('email', e.target.value)}
                                error={validationErrors.email}
                                required
                            />
                            <SelectField
                                label="System Role"
                                value={formData.role}
                                onChange={(e) => handleInputChange('role', e.target.value)}
                                options={adminOptions}
                                required
                                placeholder="Select your specific role"
                                error={validationErrors.role}
                            />
                            <SearchableSelect
                                label="Country"
                                value={formData.countryId}
                                onChange={onCountryChange}
                                options={countries.map(c => ({
                                    value: c.country_id,
                                    label: c.country_name,
                                    code: c.country_code
                                }))}
                                required
                                isCountry={true}
                                placeholder="Search for your country..."
                            />
                            <SearchableSelect
                                label="Region / State"
                                value={formData.regionId}
                                onChange={onRegionChange}
                                options={regions.map(r => ({ value: r.region_id, label: r.region_name }))}
                                required
                                disabled={!formData.countryId}
                                placeholder={!formData.countryId ? "Select country first" : "Search for your region..."}
                            />
                            <SearchableSelect
                                label="Assigned Clinical Hospital"
                                value={formData.hospitalId}
                                onChange={(e) => handleInputChange('hospitalId', e.target.value)}
                                options={hospitals.map(h => ({ value: h.hospital_id, label: h.hospital_name }))}
                                required
                                disabled={!formData.regionId}
                                error={validationErrors.hospitalId}
                                placeholder={!formData.regionId ? "Select region first" : "Search for hospitals..."}
                            />
                            <InputField
                                label="Master Security Password"
                                type="password"
                                placeholder="••••••••••••••••"
                                value={formData.password}
                                onChange={(e) => handleInputChange('password', e.target.value)}
                                error={validationErrors.password}
                                required
                            />
                            <InputField
                                label="Confirm Master Password"
                                type="password"
                                placeholder="••••••••••••••••"
                                value={formData.confirmPassword}
                                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                                error={validationErrors.confirmPassword}
                                required
                            />
                        </div>

                        <AnimatedButton
                            type="submit"
                            variant="primary"
                            size="large"
                            fullWidth
                            isLoading={isLoading}
                            style={{ marginTop: '1.5rem' }}
                        >
                            Authorize Administrator Credentials
                        </AnimatedButton>
                    </form>
                </motion.div>
            </div>
        </div>
    )
}
