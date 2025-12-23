import { motion } from 'framer-motion'
import { TopBar } from '../components/TopBar'
import { Medical3DViewer } from '../components/Medical3DViewer'
import styles from './ProjectAbout.module.css'

// Professional Icon Imports
import analyticsIcon from '../images/icons/analytics.png'
import securityIcon from '../images/icons/security.png'
import insightsIcon from '../images/icons/insights.png'

/**
 * ProjectAbout Component - Clinical Gateway
 * 
 * redesigns the entry experience to communicate system mission, 
 * technical stack, and clinical utility.
 */
export const ProjectAbout = ({ onBack }) => {

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.1, delayChildren: 0.2 }
        }
    }

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: {
            opacity: 1,
            y: 0,
            transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] }
        }
    }

    return (
        <div className={styles.pageWrapper}>
            <TopBar onBack={onBack} />

            <motion.div
                className={styles.container}
                variants={containerVariants}
                initial="hidden"
                animate="visible"
            >
                {/* Mission Critical Hero */}
                <motion.section className={styles.hero} variants={itemVariants}>
                    <h1 className={styles.title}>BioIntellect<br />Clinical Intelligence</h1>
                    <p className={styles.subtitle}>
                        A mission-critical medical platform integrating multi-modal AI diagnostics,
                        real-time volumetric 3D visualization, and enterprise-grade data security.
                    </p>
                </motion.section>

                {/* 3D Volumetric Showreel */}
                <div className={styles.showreel}>
                    {/* Cardiac Module */}
                    <motion.div className={styles.studioWrapper} variants={itemVariants}>
                        <div className={styles.viewerHeader}>
                            <span className={styles.modelName}>MODULE_01: CARDIAC_SCAN_3D</span>
                            <div className={styles.viewStatus}><span className={styles.livePulse} /> LIVE_SYNC</div>
                        </div>
                        <div className={styles.volumetricStage}>
                            <div className={styles.webglCanvasWrapper}>
                                <Medical3DViewer type="heart" />
                            </div>
                        </div>
                        <div className={styles.studioFooter}>
                            <h3>Cardiovascular Morphology</h3>
                            <p>Real-time structural assessment of myocardial integrity and valve kinematics using volumetric simulation synchronized with clinical metrics.</p>
                        </div>
                    </motion.div>

                    {/* Neural Module */}
                    <motion.div className={styles.studioWrapper} variants={itemVariants}>
                        <div className={styles.viewerHeader}>
                            <span className={styles.modelName}>MODULE_02: NEURAL_PATHWAY_3D</span>
                            <div className={styles.viewStatus}><span className={styles.livePulse} /> ACTIVE</div>
                        </div>
                        <div className={styles.volumetricStage}>
                            <div className={styles.webglCanvasWrapper}>
                                <Medical3DViewer type="brain" />
                            </div>
                        </div>
                        <div className={styles.studioFooter}>
                            <h3>Neural Synaptic Propagation</h3>
                            <p>Advanced mapping of cortical signal pathways and structural neural architecture for longitudinal diagnostic monitoring.</p>
                        </div>
                    </motion.div>
                </div>

                {/* Technical Architecture Overview */}
                <div className={styles.detailsGrid}>
                    <motion.div className={styles.detailCard} variants={itemVariants}>
                        <img src={insightsIcon} alt="Clinical LLM" className={styles.cardIcon} />
                        <h4>Advisor LLM</h4>
                        <p>Evidence-based clinical decision support trained on peer-reviewed SOPs and medical protocols.</p>
                    </motion.div>
                    <motion.div className={styles.detailCard} variants={itemVariants}>
                        <img src={analyticsIcon} alt="Diagnostics" className={styles.cardIcon} />
                        <h4>Diagnostic Engine</h4>
                        <p>Automated feature extraction from multi-source medical data for rapid triage and classification.</p>
                    </motion.div>
                    <motion.div className={styles.detailCard} variants={itemVariants}>
                        <img src={securityIcon} alt="Security" className={styles.cardIcon} />
                        <h4>Secure Gateway</h4>
                        <p>RBAC-hardened clinical data infrastructure with end-to-end encryption for patient confidentiality.</p>
                    </motion.div>
                </div>

                {/* System Purpose & Workflow */}
                <motion.section className={styles.servicesInfo} variants={itemVariants}>
                    <h2 className={styles.sectionTitle}>Integrated Workflow Integration</h2>
                    <div className={styles.servicesDisplayGrid}>
                        <div className={styles.serviceInfoCard}>
                            <h3>Who it is for</h3>
                            <p>Designed for multi-disciplinary medical teams requiring synchronized data visualization and AI-assisted triage in high-stakes environments.</p>
                        </div>
                        <div className={styles.serviceInfoCard}>
                            <h3>Production Security</h3>
                            <p>Compliance-first architecture ensuring that authentication persists securely across sessions while blocking manual route manipulation.</p>
                        </div>
                    </div>
                </motion.section>

                <footer className={styles.footer}>
                    &copy; {new Date().getFullYear()} BioIntellect Medical Intelligence. All Rights Reserved.
                </footer>
            </motion.div>
        </div>
    )
}
