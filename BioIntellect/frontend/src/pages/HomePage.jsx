import { motion } from 'framer-motion'
import { AnimatedButton } from '../components/AnimatedButton'
import { TopBar } from '../components/TopBar'
import { brandingConfig } from '../config/brandingConfig'
import styles from './HomePage.module.css'

/**
 * HomePage Component - Complete Cinematic Restoration (REVERTED)
 * 
 * Restores all functional sections (Services, Stats, Features, Contact)
 * with the centered glass portal design.
 */
export const HomePage = ({ onEnter, onAboutClick }) => {
    return (
        <div className={styles.pageWrapper}>
            <TopBar />

            {/* Cinematic Hero Section */}
            <section className={styles.hero}>
                <div className={styles.overlay} />
                <div className={styles.container}>
                    <motion.div
                        className={styles.glassPortal}
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        transition={{ duration: 1, ease: "easeOut" }}
                    >
                        <div className={styles.content}>
                            <motion.div
                                className={styles.badge}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.5 }}
                            >
                                NEXT-GEN MEDICAL INTELLIGENCE
                            </motion.div>

                            <h1 className={styles.title}>
                                {brandingConfig.brandName}
                            </h1>

                            <p className={styles.subtitle}>
                                {brandingConfig.shortDescription}
                            </p>

                            <div className={styles.ctaGroup}>
                                <AnimatedButton
                                    variant="primary"
                                    size="large"
                                    onClick={onEnter}
                                    className={styles.mainBtn}
                                >
                                    Enter System
                                </AnimatedButton>
                                <AnimatedButton
                                    variant="outline"
                                    size="large"
                                    onClick={onAboutClick}
                                    className={styles.secBtn}
                                >
                                    Project Info
                                </AnimatedButton>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Features Preview Section */}
            <section className={styles.featuresSection}>
                <div className={styles.container}>
                    <div className={styles.sectionHeader}>
                        <h2 className={styles.sectionTitle}>System Intelligence</h2>
                        <p className={styles.sectionSubtitle}>{brandingConfig.tagline}</p>
                    </div>
                    <div className={styles.featureGrid}>
                        <div className={styles.featureCard}>
                            <div className={styles.iconBox}>📊</div>
                            <h3 className={styles.featureTitle}>Clinical Analytics</h3>
                            <p className={styles.featureDesc}>Deep analysis of patient metrics using advanced neural networks and diagnostic heuristics.</p>
                        </div>
                        <div className={styles.featureCard}>
                            <div className={styles.iconBox}>🛡️</div>
                            <h3 className={styles.featureTitle}>Secure Provisioning</h3>
                            <p className={styles.featureDesc}>Enterprise-grade security for medical staff and clinical record management.</p>
                        </div>
                        <div className={styles.featureCard}>
                            <div className={styles.iconBox}>⚡</div>
                            <h3 className={styles.featureTitle}>Real-time Insights</h3>
                            <p className={styles.featureDesc}>Instant access to critical patient histories and laboratory results with zero latency.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Stats Section */}
            <section className={styles.statsSection}>
                <div className={styles.container}>
                    <div className={styles.statsGrid}>
                        <div className={styles.statItem}>
                            <h4>{brandingConfig.stats.availability}</h4>
                            <p>Critical Care</p>
                        </div>
                        <div className={styles.statItem}>
                            <h4>{brandingConfig.stats.patientsServed}</h4>
                            <p>Patients Served</p>
                        </div>
                        <div className={styles.statItem}>
                            <h4>{brandingConfig.stats.specializedStaff}</h4>
                            <p>Specialized Staff</p>
                        </div>
                        <div className={styles.statItem}>
                            <h4>{brandingConfig.stats.uptime}</h4>
                            <p>System Uptime</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Medical Services Section */}
            <section className={styles.servicesSection}>
                <div className={styles.container}>
                    <div className={styles.sectionHeader}>
                        <h2 className={styles.sectionTitle}>Clinical Departments</h2>
                        <p className={styles.sectionSubtitle}>Comprehensive medical services integrated into one platform</p>
                    </div>
                    <div className={styles.servicesGrid}>
                        {[
                            { icon: '🚑', title: 'Emergency Care' },
                            { icon: '🧪', title: 'Laboratory' },
                            { icon: '🫀', title: 'Cardiology' },
                            { icon: '🧠', title: 'Neurology' },
                            { icon: '🦴', title: 'Orthopedics' },
                            { icon: '🦷', title: 'Dental Clinic' },
                            { icon: '🍼', title: 'Pediatrics' },
                            { icon: '🩺', title: 'Internal Medicine' }
                        ].map((service, i) => (
                            <motion.div
                                key={i}
                                className={styles.serviceCard}
                                initial={{ opacity: 0, scale: 0.9 }}
                                whileInView={{ opacity: 1, scale: 1 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.05 }}
                            >
                                <span className={styles.serviceIcon}>{service.icon}</span>
                                <h4 className={styles.serviceTitle}>{service.title}</h4>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Contact & Location */}
            <section className={styles.contactSection}>
                <div className={styles.container}>
                    <h2 className={styles.sectionTitle}>Hospital Network</h2>
                    <div className={styles.contactGrid}>
                        <div className={styles.contactItem}>
                            <h5>📍 LOCATION</h5>
                            <p>{brandingConfig.contact.address}</p>
                        </div>
                        <div className={styles.contactItem}>
                            <h5>📞 CONTACT</h5>
                            <p>Support: {brandingConfig.contact.phone}<br />Emergency: {brandingConfig.contact.emergency}</p>
                        </div>
                        <div className={styles.contactItem}>
                            <h5>📧 EMAIL</h5>
                            <p>{brandingConfig.contact.email}<br />{brandingConfig.contact.supportEmail}</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className={styles.footer}>
                <div className={styles.container}>
                    &copy; {new Date().getFullYear()} {brandingConfig.brandName} - {brandingConfig.hospitalName}. All Rights Reserved.
                </div>
            </footer>
        </div>
    )
}
