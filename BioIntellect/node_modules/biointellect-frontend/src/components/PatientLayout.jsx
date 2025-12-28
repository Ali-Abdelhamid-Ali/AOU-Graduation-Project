import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { PatientSidebar } from './PatientSidebar'
import styles from './PatientLayout.module.css'

export const PatientLayout = () => {
    const [isCollapsed, setIsCollapsed] = useState(false)

    return (
        <div className={styles.layout}>
            <PatientSidebar isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed} />
            <main className={`${styles.mainContent} ${isCollapsed ? styles.expandedContent : ''}`}>
                <div className={styles.pageContainer}>
                    <Outlet />
                </div>
            </main>
        </div>
    )
}
