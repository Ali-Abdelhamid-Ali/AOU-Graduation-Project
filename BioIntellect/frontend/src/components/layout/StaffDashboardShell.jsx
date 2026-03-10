import { brandingConfig } from '@/config/brandingConfig'
import styles from './StaffDashboardShell.module.css'

const NavButton = ({ item, active, onSelect }) => {
  const statusLabel = item.available === false ? 'Unavailable' : active ? 'Current' : ''

  return (
    <button
      type="button"
      className={`${styles.navButton} ${active ? styles.navButtonActive : ''}`}
      onClick={() => item.available !== false && onSelect?.(item)}
      disabled={item.available === false}
      aria-current={active ? 'page' : undefined}
    >
      <span className={styles.navGlyph}>{item.glyph || item.label?.slice(0, 1) || '•'}</span>
      <span className={styles.navMeta}>
        <span className={styles.navLabelRow}>
          <span className={styles.navLabel}>{item.label}</span>
          {statusLabel ? <span className={styles.navStatus}>{statusLabel}</span> : null}
        </span>
        <span className={styles.navDescription}>{item.description}</span>
      </span>
    </button>
  )
}

export const StaffDashboardShell = ({
  currentUser,
  roleLabel,
  navSections = [],
  activeKey,
  onNavigate,
  searchValue,
  onSearchChange,
  notificationCount = 0,
  onLogout,
  headerTitle,
  headerSubtitle,
  children,
}) => {
  const displayName =
    currentUser?.full_name ||
    [currentUser?.first_name, currentUser?.last_name].filter(Boolean).join(' ') ||
    brandingConfig.brandName

  const profileSubtitle =
    currentUser?.specialty_name ||
    currentUser?.specialty ||
    currentUser?.hospital_name ||
    roleLabel

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar} data-print-hidden="true">
        <div className={styles.brandPanel}>
          <div className={styles.brandBadge}>BI</div>
          <div>
            <p className={styles.brandEyebrow}>{brandingConfig.hospitalName}</p>
            <h1 className={styles.brandTitle}>{brandingConfig.brandName}</h1>
          </div>
        </div>

        <div className={styles.roleCard}>
          <span className={styles.rolePill}>{roleLabel}</span>
          <strong>{displayName}</strong>
          <span>{profileSubtitle}</span>
        </div>

        <nav className={styles.navigation} aria-label="Dashboard modules">
          {navSections.map((section) => (
            <div key={section.title} className={styles.navSection}>
              <p className={styles.navSectionTitle}>{section.title}</p>
              <div className={styles.navList}>
                {section.items.map((item) => (
                  <NavButton
                    key={item.key}
                    item={item}
                    active={activeKey === item.key}
                    onSelect={onNavigate}
                  />
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <p>Medical-grade operations shell</p>
          <button type="button" className={styles.logoutButton} onClick={onLogout}>
            Log out
          </button>
        </div>
      </aside>

      <div className={styles.contentArea}>
        <header className={styles.topBar} data-print-hidden="true">
          <div className={styles.topBarCopy}>
            <p className={styles.topBarEyebrow}>{roleLabel}</p>
            <h2 className={styles.topBarTitle}>{headerTitle}</h2>
            <p className={styles.topBarSubtitle}>{headerSubtitle}</p>
          </div>

          <div className={styles.topBarActions}>
            <label className={styles.searchField}>
              <span className="sr-only">Search dashboard</span>
              <input
                type="search"
                value={searchValue}
                onChange={(event) => onSearchChange?.(event.target.value)}
                placeholder="Search users, cases, or IDs"
              />
            </label>

            <button type="button" className={styles.notificationButton} aria-label="Notifications">
              <span>Notifications</span>
              <strong>{notificationCount}</strong>
            </button>

            <div className={styles.profileChip}>
              <span className={styles.profileAvatar}>{displayName.slice(0, 2).toUpperCase()}</span>
              <div>
                <strong>{displayName}</strong>
                <span>{profileSubtitle}</span>
              </div>
            </div>
          </div>
        </header>

        <main className={styles.mainContent}>{children}</main>
      </div>
    </div>
  )
}

export default StaffDashboardShell
