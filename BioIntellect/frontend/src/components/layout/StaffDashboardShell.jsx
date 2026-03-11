import { useEffect, useMemo, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'

import { brandingConfig } from '@/config/brandingConfig'
import styles from './StaffDashboardShell.module.css'

const isItemRouteActive = (item, pathname) => {
  if (!item?.route) return false
  if (pathname === item.route) return true
  return item.matchNested ? pathname.startsWith(`${item.route}/`) : false
}

const NavButton = ({ item, active, isCollapsed, onSelect }) => {
  const statusLabel = item.available === false ? 'Unavailable' : item.badge || (active ? 'Current' : '')
  const buttonClassName = `${styles.navButton} ${active ? styles.navButtonActive : ''}`

  const content = (
    <>
      <span className={styles.navGlyph}>{item.glyph || item.label?.slice(0, 1) || '#'}</span>
      <span className={styles.navMeta}>
        <span className={styles.navLabelRow}>
          <span className={styles.navLabel}>{item.label}</span>
          {statusLabel ? <span className={styles.navStatus}>{statusLabel}</span> : null}
        </span>
        <span className={styles.navDescription}>{item.description}</span>
      </span>
    </>
  )

  if (item.route && item.available !== false) {
    return (
      <NavLink
        to={item.route}
        className={buttonClassName}
        onClick={() => onSelect?.(item)}
        aria-current={active ? 'page' : undefined}
        title={isCollapsed ? item.label : undefined}
      >
        {content}
      </NavLink>
    )
  }

  return (
    <button
      type="button"
      className={buttonClassName}
      onClick={() => item.available !== false && onSelect?.(item)}
      disabled={item.available === false}
      aria-current={active ? 'page' : undefined}
      title={isCollapsed ? item.label : undefined}
    >
      {content}
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
  notificationItems = [],
  notificationActionLabel = 'Open notifications',
  onNotificationAction,
  onLogout,
  headerTitle,
  headerSubtitle,
  searchPlaceholder = 'Search users, patients, cases, or IDs',
  searchLabel = 'Search dashboard',
  notificationLabel = 'Notifications',
  children,
}) => {
  const location = useLocation()
  const displayName =
    currentUser?.full_name ||
    [currentUser?.first_name, currentUser?.last_name].filter(Boolean).join(' ') ||
    brandingConfig.brandName

  const profileInitials =
    displayName
      .split(' ')
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0])
      .join('')
      .toUpperCase() || 'BI'

  const profileSubtitle =
    currentUser?.specialty_name ||
    currentUser?.specialty ||
    currentUser?.hospital_name ||
    roleLabel

  const storageKey = useMemo(
    () => `staff-shell-collapsed:${roleLabel.toLowerCase().replace(/\s+/g, '-')}`,
    [roleLabel]
  )

  const [isCollapsed, setIsCollapsed] = useState(() => {
    if (typeof window === 'undefined') return false
    return window.localStorage.getItem(storageKey) === 'true'
  })
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(storageKey, String(isCollapsed))
    }
  }, [isCollapsed, storageKey])

  useEffect(() => {
    setIsNotificationsOpen(false)
  }, [location.pathname])

  return (
    <div
      className={`${styles.shell} ${isCollapsed ? styles.collapsed : ''}`}
      style={{ '--staff-sidebar-width': isCollapsed ? '104px' : '312px' }}
    >
      <aside className={styles.sidebar} data-print-hidden="true">
        <div className={styles.topSection}>
          <div className={styles.brandPanel}>
            <div className={styles.brandBadge}>BI</div>
            <div className={styles.brandCopy}>
              <p className={styles.brandEyebrow}>{brandingConfig.hospitalName}</p>
              <h1 className={styles.brandTitle}>{brandingConfig.brandName}</h1>
            </div>
          </div>

          <button
            type="button"
            className={styles.collapseToggle}
            onClick={() => setIsCollapsed((previous) => !previous)}
            aria-label={isCollapsed ? 'Expand staff navigation' : 'Collapse staff navigation'}
          >
            {isCollapsed ? '+' : '-'}
          </button>
        </div>

        <div className={styles.roleCard}>
          <div className={styles.roleIdentity}>
            <span className={styles.roleAvatar}>{profileInitials}</span>
            <div className={styles.roleCopy}>
              <span className={styles.rolePill}>{roleLabel}</span>
              <strong>{displayName}</strong>
              <span>{profileSubtitle}</span>
            </div>
          </div>
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
                    active={item.route ? isItemRouteActive(item, location.pathname) : activeKey === item.key}
                    isCollapsed={isCollapsed}
                    onSelect={onNavigate}
                  />
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <p>Medical-grade operations shell</p>
          <button type="button" className={styles.logoutButton} onClick={() => onLogout?.()}>
            <span className={styles.logoutGlyph}>LO</span>
            <span className={styles.logoutLabel}>Log out</span>
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
              <span className="sr-only">{searchLabel}</span>
              <input
                type="search"
                value={searchValue}
                onChange={(event) => onSearchChange?.(event.target.value)}
                placeholder={searchPlaceholder}
              />
            </label>

            <div className={styles.notificationGroup}>
              <button
                type="button"
                className={styles.notificationButton}
                aria-label={notificationLabel}
                aria-expanded={isNotificationsOpen}
                onClick={() => setIsNotificationsOpen((previous) => !previous)}
              >
                <span>{notificationLabel}</span>
                <strong>{notificationCount}</strong>
              </button>

              {isNotificationsOpen ? (
                <div className={styles.notificationPanel} role="dialog" aria-label={notificationLabel}>
                  <div className={styles.notificationPanelHeader}>
                    <div>
                      <strong>{notificationLabel}</strong>
                      <p>{notificationCount ? `${notificationCount} item(s) need review` : 'No new items right now'}</p>
                    </div>
                    {onNotificationAction ? (
                      <button
                        type="button"
                        className={styles.notificationPanelAction}
                        onClick={() => {
                          setIsNotificationsOpen(false)
                          onNotificationAction()
                        }}
                      >
                        {notificationActionLabel}
                      </button>
                    ) : null}
                  </div>

                  {notificationItems.length ? (
                    <div className={styles.notificationList}>
                      {notificationItems.map((item, index) => (
                        <div key={item.id || `${item.title}-${index}`} className={styles.notificationRow}>
                          <div className={styles.notificationRowBody}>
                            <strong>{item.title}</strong>
                            <p>{item.message}</p>
                          </div>
                          <span>{item.time || item.time_ago || item.timestamp || 'Recent'}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className={styles.notificationEmpty}>
                      <strong>Inbox is clear</strong>
                      <p>No alerts or notices are waiting for review.</p>
                    </div>
                  )}
                </div>
              ) : null}
            </div>

            <div className={styles.profileChip}>
              <span className={styles.profileAvatar}>{profileInitials}</span>
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
