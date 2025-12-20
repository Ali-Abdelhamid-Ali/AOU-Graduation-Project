import { motion } from 'framer-motion'
import { TopBar } from '../components/TopBar'
import { brandingConfig } from '../config/brandingConfig'
import styles from './ProjectAbout.module.css'

export const ProjectAbout = ({ onBack }) => {
    return (
        <div className={styles.pageWrapper}>
            <TopBar onBack={onBack} />

            <div className={styles.container}>
                <section className={styles.hero}>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={styles.academicBadge}
                    >
                        ARAB OPEN UNIVERSITY - EGYPT
                    </motion.div>
                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className={styles.title}
                    >
                        BioIntellect: An AI-Based Diagnostic System for Heart and Brain Diseases
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className={styles.subtitle}
                    >
                        Faculty of Computer Studies | TM471 - Final Year Project, Fall 2025-2026
                    </motion.p>
                </section>

                <div className={styles.contentGrid}>
                    {/* Team Section */}
                    <motion.section
                        className={styles.card}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 }}
                    >
                        <h3>🎓 Project Team</h3>
                        <div className={styles.teamMember}>
                            <strong>Student:</strong>
                            <span>Ali Abdelhamid Ali</span>
                            <small>ID: 22510786</small>
                        </div>
                        <div className={styles.teamMember}>
                            <strong>Supervisor:</strong>
                            <span>Dr. Eid Emary</span>
                        </div>
                    </motion.section>

                    {/* Abstract Section */}
                    <motion.section
                        className={styles.card + ' ' + styles.mainCard}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                    >
                        <h3>📄 Abstract</h3>
                        <p>
                            Cardiovascular and neurological diseases remain among the leading causes of mortality worldwide.
                            Timely and accurate diagnosis is critical for effective clinical intervention.
                            BioIntellect is a comprehensive AI-based diagnostic system designed to assist physicians in the early detection and classification of heart and brain diseases through multimodal data analysis.
                        </p>
                    </motion.section>

                    {/* Technical Stack */}
                    <motion.section
                        className={styles.card}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.5 }}
                    >
                        <h3>⚙️ Technical Deliverables</h3>
                        <ul className={styles.list}>
                            <li>Deep learning models for ECG arrhythmia classification</li>
                            <li>3D segmentation models for brain tumor detection</li>
                            <li>Fine-tuned medical language model for clinical QA</li>
                            <li>Web-based physician interface</li>
                        </ul>
                    </motion.section>

                    {/* Aim and Objectives */}
                    <motion.section
                        className={styles.card + ' ' + styles.wideCard}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.6 }}
                    >
                        <h3>🎯 Aims and Objectives</h3>
                        <div className={styles.objectivesGrid}>
                            <div className={styles.objItem}>
                                <span>01</span>
                                <p>Design an AI system processing ECG signals and MRI images.</p>
                            </div>
                            <div className={styles.objItem}>
                                <span>02</span>
                                <p>Develop deep learning models for cardiac arrhythmia classification.</p>
                            </div>
                            <div className={styles.objItem}>
                                <span>03</span>
                                <p>Implement 3D segmentation algorithms for brain tumor detection.</p>
                            </div>
                            <div className={styles.objItem}>
                                <span>04</span>
                                <p>Create a web interface for data upload and result visualization.</p>
                            </div>
                        </div>
                    </motion.section>

                    {/* Acknowledgements */}
                    <motion.section
                        className={styles.card + ' ' + styles.wideCard}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.7 }}
                    >
                        <h3>🙏 Acknowledgements</h3>
                        <p className={styles.ackText}>
                            Sincere gratitude to my supervisor, <strong>Dr. Eid Emary</strong>, for his continuous guidance,
                            and the Faculty of Computer Studies at the <strong>Arab Open University</strong> for enabling this research.
                        </p>
                    </motion.section>
                </div>
            </div>

            <footer className={styles.footer}>
                &copy; {new Date().getFullYear()} BioIntellect - Arab Open University (AOU-Egypt)
            </footer>
        </div>
    )
}
