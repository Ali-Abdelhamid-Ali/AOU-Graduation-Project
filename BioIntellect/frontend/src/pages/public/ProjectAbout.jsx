import { Suspense, lazy } from 'react'
import { motion } from 'framer-motion'
import { TopBar } from '@/components/layout/TopBar'
import styles from './ProjectAbout.module.css'

import analyticsIcon from '@/assets/images/icons/analytics.png'
import securityIcon from '@/assets/images/icons/security.png'
import insightsIcon from '@/assets/images/icons/insights.png'

const ProjectInfoModelViewer = lazy(() =>
    import('../../components/clinical/ProjectInfoModelViewer').then((module) => ({
        default: module.ProjectInfoModelViewer,
    }))
)

const fadeUp = {
    hidden: { opacity: 0, y: 32 },
    visible: (i = 0) => ({
        opacity: 1,
        y: 0,
        transition: { duration: 0.65, ease: [0.22, 1, 0.36, 1], delay: i * 0.1 },
    }),
}

const stagger = {
    hidden: {},
    visible: { transition: { staggerChildren: 0.1, delayChildren: 0.15 } },
}

const WHY_ITEMS = [
    {
        icon: '⚡',
        title: 'Results in minutes, not days',
        body: 'Upload your scan or ECG recording and get a detailed, easy-to-read analysis within minutes — no waiting rooms, no scheduling delays.',
    },
    {
        icon: '🧠',
        title: 'AI that speaks your language',
        body: 'Our assistant translates complex medical findings into plain English so you always understand what is happening with your health.',
    },
    {
        icon: '🔒',
        title: 'Your data belongs to you',
        body: 'Every record is encrypted end-to-end. Only you and your assigned medical team can access your information — ever.',
    },
    {
        icon: '📋',
        title: 'Everything in one place',
        body: 'Reports, scan history, appointments, and your medical chat — unified in a single platform designed around your journey.',
    },
]

const HOW_IT_WORKS = [
    {
        step: '01',
        title: 'Upload or connect',
        body: 'Share your ECG file, MRI scan, or clinical report directly through the platform.',
    },
    {
        step: '02',
        title: 'AI analyses instantly',
        body: 'Our models process your data and surface key findings, anomalies, and patterns.',
    },
    {
        step: '03',
        title: 'Your doctor reviews',
        body: 'The findings are forwarded to your care team with full context for a professional decision.',
    },
    {
        step: '04',
        title: 'You understand your health',
        body: 'A clear summary lands in your portal — no jargon, no confusion.',
    },
]

export const ProjectAbout = ({ onBack }) => {
    return (
        <div className={styles.pageWrapper}>
            <TopBar onBack={onBack} />

            {/* ── HERO ── */}
            <section className={styles.hero}>
                <div className={styles.heroBg} aria-hidden="true">
                    <div className={styles.orb1} />
                    <div className={styles.orb2} />
                    <div className={styles.orb3} />
                    <div className={styles.gridLines} />
                </div>

                <motion.div
                    className={styles.heroContent}
                    variants={stagger}
                    initial="hidden"
                    animate="visible"
                >
                    <motion.div className={styles.heroBadge} variants={fadeUp} custom={0}>
                        <span className={styles.badgeDot} />
                        Powered by Medical-Grade AI
                    </motion.div>

                    <motion.h1 className={styles.heroTitle} variants={fadeUp} custom={1}>
                        Your health, <br />
                        <span className={styles.gradientText}>understood.</span>
                    </motion.h1>

                    <motion.p className={styles.heroSubtitle} variants={fadeUp} custom={2}>
                        BioIntellect gives you instant access to intelligent analysis of your heart and brain scans,
                        a 24/7 medical assistant, and a secure home for your entire health record —
                        all reviewed by your dedicated care team.
                    </motion.p>

                    <motion.div className={styles.heroStats} variants={fadeUp} custom={3}>
                        <div className={styles.stat}>
                            <span className={styles.statNum}>3</span>
                            <span className={styles.statLabel}>AI Diagnostic Modules</span>
                        </div>
                        <div className={styles.statDivider} />
                        <div className={styles.stat}>
                            <span className={styles.statNum}>24/7</span>
                            <span className={styles.statLabel}>Medical Assistant</span>
                        </div>
                        <div className={styles.statDivider} />
                        <div className={styles.stat}>
                            <span className={styles.statNum}>100%</span>
                            <span className={styles.statLabel}>Private & Encrypted</span>
                        </div>
                    </motion.div>
                </motion.div>
            </section>

            {/* ── 3D VIEWERS ── */}
            <section className={styles.viewersSection}>
                <motion.div
                    className={styles.viewersSectionHeader}
                    variants={stagger}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                >
                    <motion.p className={styles.sectionEyebrow} variants={fadeUp}>Diagnostic Imaging</motion.p>
                    <motion.h2 className={styles.sectionTitle} variants={fadeUp}>
                        See inside, understand more
                    </motion.h2>
                    <motion.p className={styles.sectionBody} variants={fadeUp}>
                        Interactive 3D models help you and your doctor visualise exactly what is happening
                        — no more staring at grey-scale images that mean nothing to you.
                    </motion.p>
                </motion.div>

                <div className={styles.showreel}>
                    {/* Heart */}
                    <motion.div
                        className={`${styles.viewerCard} ${styles.heartCard}`}
                        initial={{ opacity: 0, x: -40 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true, amount: 0.2 }}
                        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
                    >
                        <div className={styles.viewerGlow} data-color="heart" aria-hidden="true" />
                        <div className={styles.viewerHeader}>
                            <div className={styles.viewerMeta}>
                                <span className={styles.viewerPulse} data-color="heart" />
                                <span className={styles.viewerTag}>Cardiovascular</span>
                            </div>
                            <span className={styles.viewerLive}>Live 3D</span>
                        </div>
                        <div className={styles.volumetricStage}>
                            <div className={styles.webglCanvasWrapper}>
                                <Suspense fallback={null}>
                                    <ProjectInfoModelViewer type="heart" />
                                </Suspense>
                            </div>
                        </div>
                        <div className={styles.viewerFooter}>
                            <h3 className={styles.viewerFooterTitle}>Heart Health Analysis</h3>
                            <p className={styles.viewerFooterBody}>
                                An interactive model of your cardiac structure helps your doctor explain findings
                                clearly, and helps you ask the right questions.
                            </p>
                        </div>
                    </motion.div>

                    {/* Brain */}
                    <motion.div
                        className={`${styles.viewerCard} ${styles.brainCard}`}
                        initial={{ opacity: 0, x: 40 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true, amount: 0.2 }}
                        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1], delay: 0.1 }}
                    >
                        <div className={styles.viewerGlow} data-color="brain" aria-hidden="true" />
                        <div className={styles.viewerHeader}>
                            <div className={styles.viewerMeta}>
                                <span className={styles.viewerPulse} data-color="brain" />
                                <span className={styles.viewerTag}>Neurological</span>
                            </div>
                            <span className={styles.viewerLive}>Live 3D</span>
                        </div>
                        <div className={styles.volumetricStage}>
                            <div className={styles.webglCanvasWrapper}>
                                <Suspense fallback={null}>
                                    <ProjectInfoModelViewer type="brain" />
                                </Suspense>
                            </div>
                        </div>
                        <div className={styles.viewerFooter}>
                            <h3 className={styles.viewerFooterTitle}>Brain MRI Interpretation</h3>
                            <p className={styles.viewerFooterBody}>
                                We analyse MRI scans and surface key structural findings, giving your care team
                                a richer picture without the wait.
                            </p>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* ── WHAT WE DO ── */}
            <section className={styles.featuresSection}>
                <motion.div
                    className={styles.featuresSectionHeader}
                    variants={stagger}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                >
                    <motion.p className={styles.sectionEyebrow} variants={fadeUp}>The Platform</motion.p>
                    <motion.h2 className={styles.sectionTitle} variants={fadeUp}>
                        Three tools. One complete picture.
                    </motion.h2>
                </motion.div>

                <motion.div
                    className={styles.featuresGrid}
                    variants={stagger}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.2 }}
                >
                    <motion.div className={`${styles.featureCard} ${styles.featureCardLarge}`} variants={fadeUp}>
                        <div className={styles.featureIconWrap} data-accent="blue">
                            <img src={insightsIcon} alt="" className={styles.featureIcon} />
                        </div>
                        <h3 className={styles.featureTitle}>Medical AI Assistant</h3>
                        <p className={styles.featureBody}>
                            Ask any health question and get an answer grounded in peer-reviewed medical knowledge.
                            Available around the clock, with no appointment needed. Think of it as having a
                            knowledgeable friend who happens to know medicine — always ready, never rushed.
                        </p>
                        <ul className={styles.featurePills}>
                            <li>Symptom guidance</li>
                            <li>Report explanation</li>
                            <li>Medication queries</li>
                        </ul>
                    </motion.div>

                    <motion.div className={`${styles.featureCard} ${styles.featureCardLarge}`} variants={fadeUp} custom={1}>
                        <div className={styles.featureIconWrap} data-accent="red">
                            <img src={analyticsIcon} alt="" className={styles.featureIcon} />
                        </div>
                        <h3 className={styles.featureTitle}>Diagnostic Intelligence</h3>
                        <p className={styles.featureBody}>
                            Upload your ECG recording or brain MRI and our AI surfaces key patterns within minutes.
                            Every finding is presented alongside a plain-English summary — because
                            understanding your results should not require a medical degree.
                        </p>
                        <ul className={styles.featurePills}>
                            <li>ECG rhythm analysis</li>
                            <li>MRI segmentation</li>
                            <li>Pattern detection</li>
                        </ul>
                    </motion.div>

                    <motion.div className={styles.featureCard} variants={fadeUp} custom={2}>
                        <div className={styles.featureIconWrap} data-accent="green">
                            <img src={securityIcon} alt="" className={styles.featureIcon} />
                        </div>
                        <h3 className={styles.featureTitle}>Secure Health Record</h3>
                        <p className={styles.featureBody}>
                            Every report, scan, and appointment lives in one encrypted, private space.
                            Only you and your care team can see it.
                        </p>
                    </motion.div>

                    <motion.div className={styles.featureCard} variants={fadeUp} custom={3}>
                        <div className={`${styles.featureIconWrap} ${styles.featureIconEmoji}`} data-accent="purple">
                            <span>👥</span>
                        </div>
                        <h3 className={styles.featureTitle}>Your Care Team, Connected</h3>
                        <p className={styles.featureBody}>
                            Doctors review every AI finding before any decision is made.
                            You always have a human in the loop.
                        </p>
                    </motion.div>
                </motion.div>
            </section>

            {/* ── HOW IT WORKS ── */}
            <section className={styles.howSection}>
                <div className={styles.howInner}>
                    <motion.div
                        variants={stagger}
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                    >
                        <motion.p className={styles.sectionEyebrow} variants={fadeUp}>How It Works</motion.p>
                        <motion.h2 className={styles.sectionTitle} variants={fadeUp}>
                            From upload to understanding<br />in four steps
                        </motion.h2>
                    </motion.div>

                    <motion.div
                        className={styles.howGrid}
                        variants={stagger}
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.2 }}
                    >
                        {HOW_IT_WORKS.map(({ step, title, body }) => (
                            <motion.div key={step} className={styles.howCard} variants={fadeUp}>
                                <span className={styles.howStep}>{step}</span>
                                <h4 className={styles.howTitle}>{title}</h4>
                                <p className={styles.howBody}>{body}</p>
                            </motion.div>
                        ))}
                    </motion.div>
                </div>
            </section>

            {/* ── WHY BIOINTELLECT ── */}
            <section className={styles.whySection}>
                <motion.div
                    className={styles.whySectionHeader}
                    variants={stagger}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                >
                    <motion.p className={styles.sectionEyebrow} variants={fadeUp}>Why BioIntellect</motion.p>
                    <motion.h2 className={styles.sectionTitle} variants={fadeUp}>
                        The care experience<br />you actually deserve
                    </motion.h2>
                    <motion.p className={styles.sectionBody} variants={fadeUp}>
                        You deserve more than a ten-minute appointment and a report you cannot read.
                        BioIntellect gives you clarity, speed, and a care team that is always informed.
                    </motion.p>
                </motion.div>

                <motion.div
                    className={styles.whyGrid}
                    variants={stagger}
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.2 }}
                >
                    {WHY_ITEMS.map(({ icon, title, body }, i) => (
                        <motion.div key={title} className={styles.whyCard} variants={fadeUp} custom={i}>
                            <span className={styles.whyIcon}>{icon}</span>
                            <h4 className={styles.whyTitle}>{title}</h4>
                            <p className={styles.whyBody}>{body}</p>
                        </motion.div>
                    ))}
                </motion.div>
            </section>

            {/* ── CTA BANNER ── */}
            <motion.section
                className={styles.ctaSection}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.4 }}
                transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            >
                <div className={styles.ctaBg} aria-hidden="true">
                    <div className={styles.ctaOrb1} />
                    <div className={styles.ctaOrb2} />
                </div>
                <div className={styles.ctaContent}>
                    <h2 className={styles.ctaTitle}>Your health journey starts here.</h2>
                    <p className={styles.ctaBody}>
                        Sign in to access your personal health portal, your AI assistant,
                        and your complete diagnostic history — all in one secure place.
                    </p>
                </div>
            </motion.section>

            <footer className={styles.footer}>
                &copy; {new Date().getFullYear()} BioIntellect Medical Intelligence. All Rights Reserved.
            </footer>
        </div>
    )
}
