import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/store/AuthContext'
import { TopBar } from '@/components/layout/TopBar'
import { AnimatedButton } from '@/components/ui/AnimatedButton'
import { patientsAPI } from '@/services/api'
import styles from './PatientDirectory.module.css'

export const PatientDirectory = ({ onBack }) => {
    const { userRole } = useAuth()
    const [searchQuery, setSearchQuery] = useState('')
    const [isSearching, setIsSearching] = useState(false)
    const [patients, setPatients] = useState([])
    const [selectedPatient, setSelectedPatient] = useState(null)
    const [isEditing, setIsEditing] = useState(false)
    const [editData, setEditData] = useState({})
    const [saveStatus, setSaveStatus] = useState(null) // 'saving', 'success', 'error'

    const handleSearch = async (e) => {
        if (e) e.preventDefault()
        if (!searchQuery.trim()) return

        setIsSearching(true)
        setSelectedPatient(null)
        setPatients([])

        try {
            const response = await patientsAPI.list({ search: searchQuery })
            if (response.success) {
                setPatients(response.data || [])
            }
        } catch (err) {
            console.error('Search Error:', err)
        } finally {
            setIsSearching(false)
        }
    }

    const loadPatientDetail = async (patient) => {
        setSelectedPatient(patient)
        setEditData({ ...patient })
        setIsEditing(false)
        setSaveStatus(null)
        window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    const handleSave = async () => {
        setSaveStatus('saving')
        try {
            const updatePayload = {
                first_name: editData.first_name,
                last_name: editData.last_name,
                phone: editData.phone,
                address: editData.address,
                emergency_contact_name: editData.emergency_contact_name,
                emergency_contact_phone: editData.emergency_contact_phone,
                notes: editData.notes,
                gender: editData.gender,
                blood_type: editData.blood_type
            }

            const response = await patientsAPI.update(selectedPatient.user_id || selectedPatient.id, updatePayload)
            if (!response.success) throw new Error('Update failed')

            setSaveStatus('success')
            setSelectedPatient({ ...selectedPatient, ...editData })
            setIsEditing(false)

            setTimeout(() => setSaveStatus(null), 3000)
        } catch (err) {
            console.error('Update Error:', err)
            setSaveStatus('error')
        }
    }

    return (
        <div className={styles.pageWrapper}>
            <TopBar onBack={onBack} userRole={userRole} />

            <div className={styles.container}>
                <header className={styles.header}>
                    <div className={styles.breadcrumb}>SYSTEM / CLINICAL_RECORDS / DIRECTORY</div>
                    <h1>Patient Management Center</h1>
                    <p>Securely access and manage patient administrative and clinical records.</p>
                </header>

                <div className={styles.searchSection}>
                    <form onSubmit={handleSearch} className={styles.searchBar}>
                        <input
                            type="text"
                            placeholder="Search by MRN, Name, or Phone Number..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                        <button type="submit" disabled={isSearching}>
                            {isSearching ? 'SEARCHING...' : 'SEARCH'}
                        </button>
                    </form>
                </div>

                <div className={styles.mainGrid}>
                    {/* Left Panel: Search Results */}
                    <aside className={styles.resultsPanel}>
                        <h3>Results ({patients.length})</h3>
                        <div className={styles.patientList}>
                            {patients.length > 0 ? (
                                patients.map(p => (
                                    <motion.div
                                        key={p.id}
                                        className={`${styles.patientItem} ${selectedPatient?.id === p.id ? styles.selected : ''}`}
                                        onClick={() => loadPatientDetail(p)}
                                        whileHover={{ x: 5 }}
                                    >
                                        <div className={styles.patientAvatar}>
                                            {p.first_name[0]}{p.last_name[0]}
                                        </div>
                                        <div className={styles.patientInfo}>
                                            <div className={styles.pName}>{p.first_name} {p.last_name}</div>
                                            <div className={styles.pMrn}>{p.medical_record_number}</div>
                                        </div>
                                        <div className={styles.arrow}>&rarr;</div>
                                    </motion.div>
                                ))
                            ) : (
                                <div className={styles.emptyResults}>
                                    {isSearching ? 'Searching clinical database...' : 'Enter query to begin search'}
                                </div>
                            )}
                        </div>
                    </aside>

                    {/* Right Panel: Patient Profile & Editor */}
                    <main className={styles.detailPanel}>
                        <AnimatePresence mode="wait">
                            {selectedPatient ? (
                                <motion.div
                                    key={selectedPatient.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -10 }}
                                    className={styles.profileCard}
                                >
                                    <div className={styles.cardHeader}>
                                        <div className={styles.headerTitle}>
                                            <span className={styles.statusBadge}>ACTIVE_RECORD</span>
                                            <h2>{selectedPatient.first_name} {selectedPatient.last_name}</h2>
                                            <span className={styles.mrnTag}>MRN: {selectedPatient.medical_record_number}</span>
                                        </div>
                                        <div className={styles.headerActions}>
                                            {!isEditing ? (
                                                <button
                                                    className={styles.editBtn}
                                                    onClick={() => setIsEditing(true)}
                                                >
                                                    EDIT PROFILE
                                                </button>
                                            ) : (
                                                <div className={styles.editActions}>
                                                    <button
                                                        className={styles.cancelBtn}
                                                        onClick={() => setIsEditing(false)}
                                                    >
                                                        CANCEL
                                                    </button>
                                                    <button
                                                        className={styles.saveBtn}
                                                        onClick={handleSave}
                                                        disabled={saveStatus === 'saving'}
                                                    >
                                                        {saveStatus === 'saving' ? 'SAVING...' : 'SAVE CHANGES'}
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {saveStatus === 'success' && (
                                        <div className={styles.successMsg}>Record updated successfully.</div>
                                    )}

                                    <div className={styles.profileGrid}>
                                        <section className={styles.fieldSection}>
                                            <h4>Identification & Demographics</h4>
                                            <div className={styles.fieldGrid}>
                                                <div className={styles.field}>
                                                    <label>First Name</label>
                                                    {isEditing ? <input value={editData.first_name} onChange={e => setEditData({ ...editData, first_name: e.target.value })} /> : <span>{selectedPatient.first_name}</span>}
                                                </div>
                                                <div className={styles.field}>
                                                    <label>Last Name</label>
                                                    {isEditing ? <input value={editData.last_name} onChange={e => setEditData({ ...editData, last_name: e.target.value })} /> : <span>{selectedPatient.last_name}</span>}
                                                </div>
                                                <div className={styles.field}>
                                                    <label>Date of Birth</label>
                                                    <span>{selectedPatient.date_of_birth || 'N/A'}</span>
                                                </div>
                                                <div className={styles.field}>
                                                    <label>Gender</label>
                                                    {isEditing ? (
                                                        <select value={editData.gender} onChange={e => setEditData({ ...editData, gender: e.target.value })}>
                                                            <option value="male">Male</option>
                                                            <option value="female">Female</option>
                                                            <option value="other">Other</option>
                                                        </select>
                                                    ) : <span className={styles.capitalize}>{selectedPatient.gender}</span>}
                                                </div>
                                            </div>
                                        </section>

                                        <section className={styles.fieldSection}>
                                            <h4>Contact Information</h4>
                                            <div className={styles.fieldGrid}>
                                                <div className={styles.field}>
                                                    <label>Primary Phone</label>
                                                    {isEditing ? <input value={editData.phone} onChange={e => setEditData({ ...editData, phone: e.target.value })} /> : <span>{selectedPatient.phone || 'N/A'}</span>}
                                                </div>
                                                <div className={styles.field}>
                                                    <label>Residential Address</label>
                                                    {isEditing ? <input value={editData.address} onChange={e => setEditData({ ...editData, address: e.target.value })} /> : <span>{selectedPatient.address || 'N/A'}</span>}
                                                </div>
                                            </div>
                                        </section>

                                        <section className={styles.fieldSection}>
                                            <h4>Emergency Contact</h4>
                                            <div className={styles.fieldGrid}>
                                                <div className={styles.field}>
                                                    <label>Full Name</label>
                                                    {isEditing ? <input value={editData.emergency_contact_name} onChange={e => setEditData({ ...editData, emergency_contact_name: e.target.value })} /> : <span>{selectedPatient.emergency_contact_name || 'N/A'}</span>}
                                                </div>
                                                <div className={styles.field}>
                                                    <label>Phone Number</label>
                                                    {isEditing ? <input value={editData.emergency_contact_phone} onChange={e => setEditData({ ...editData, emergency_contact_phone: e.target.value })} /> : <span>{selectedPatient.emergency_contact_phone || 'N/A'}</span>}
                                                </div>
                                            </div>
                                        </section>

                                        <section className={styles.fieldSection}>
                                            <h4>Clinical Notes</h4>
                                            <div className={styles.fieldFull}>
                                                {isEditing ? (
                                                    <textarea
                                                        value={editData.notes || ''}
                                                        onChange={e => setEditData({ ...editData, notes: e.target.value })}
                                                        placeholder="Enter clinical or administrative notes..."
                                                    />
                                                ) : <p className={styles.notesBox}>{selectedPatient.notes || 'No active notes for this patient.'}</p>}
                                            </div>
                                        </section>
                                    </div>
                                </motion.div>
                            ) : (
                                <div className={styles.emptyDetail}>
                                    <div className={styles.placeholderIcon}>📋</div>
                                    <h3>Patient Profile Viewer</h3>
                                    <p>Select a patient from the search results to view and edit their complete medical and administrative record.</p>
                                </div>
                            )}
                        </AnimatePresence>
                    </main>
                </div>
            </div>
        </div>
    )
}

export default PatientDirectory
