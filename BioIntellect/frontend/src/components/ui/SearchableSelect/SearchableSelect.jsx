import React, { useState, useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styles from './SearchableSelect.module.css';

/**
 * SearchableSelect
 * A premium, high-performance searchable dropdown.
 *
 * Features:
 * - Full-text search across label, code, region, subregion
 * - Flag support via flagcdn.com (isCountry=true)
 * - Region / subregion badge per country option
 * - Region group headers when no search term is active
 * - Accessible click-outside closing
 * - Works for both country and non-country dropdowns
 *
 * Option shape (country):
 *   { value, label, code, flag_url?, region?, subregion? }
 */
const SearchableSelect = ({
    label,
    value,
    onChange,
    options = [],
    required = false,
    disabled = false,
    placeholder = 'Select an option...',
    isCountry = false,
    error = null,
}) => {
    const [isOpen, setIsOpen]     = useState(false);
    const [searchTerm, setSearch] = useState('');
    const containerRef            = useRef(null);
    const inputRef                = useRef(null);
    const listRef                 = useRef(null);

    // ── Close on outside click ──────────────────────────────────────────
    useEffect(() => {
        const handle = (e) => {
            if (containerRef.current && !containerRef.current.contains(e.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handle);
        return () => document.removeEventListener('mousedown', handle);
    }, []);

    // ── Auto-focus search on open ───────────────────────────────────────
    useEffect(() => {
        if (isOpen && inputRef.current) inputRef.current.focus();
    }, [isOpen]);

    // ── Selected option ─────────────────────────────────────────────────
    const selectedOption = useMemo(
        () => options.find((o) => o.value === value),
        [options, value]
    );

    // ── Filtered list ───────────────────────────────────────────────────
    const filteredOptions = useMemo(() => {
        if (!searchTerm.trim()) return options;
        const q = searchTerm.toLowerCase();
        return options.filter(
            (o) =>
                o.label.toLowerCase().includes(q) ||
                (o.code  && o.code.toLowerCase().includes(q))  ||
                (o.region    && o.region.toLowerCase().includes(q)) ||
                (o.subregion && o.subregion.toLowerCase().includes(q))
        );
    }, [options, searchTerm]);

    // ── Group by region when showing countries without a search ─────────
    const grouped = useMemo(() => {
        if (!isCountry || searchTerm.trim()) return null; // flat list when searching

        const map = new Map();
        for (const opt of filteredOptions) {
            const key = opt.region || 'Other';
            if (!map.has(key)) map.set(key, []);
            map.get(key).push(opt);
        }
        // Sort regions: Middle East first for medical audience, then alphabetical
        const REGION_ORDER = ['Asia', 'Africa', 'Europe', 'Americas', 'Oceania', 'Other'];
        const sorted = [...map.entries()].sort(
            ([a], [b]) => {
                const ai = REGION_ORDER.indexOf(a);
                const bi = REGION_ORDER.indexOf(b);
                if (ai === -1 && bi === -1) return a.localeCompare(b);
                if (ai === -1) return 1;
                if (bi === -1) return -1;
                return ai - bi;
            }
        );
        return sorted;
    }, [isCountry, searchTerm, filteredOptions]);

    const getFlagUrl = (code) =>
        code ? `https://flagcdn.com/w40/${code.toLowerCase()}.png` : null;

    const handleSelect = (option) => {
        onChange({ target: { value: option.value, name: label } });
        setIsOpen(false);
        setSearch('');
    };

    const renderOption = (option) => (
        <div
            key={option.value}
            className={`${styles.optionItem} ${value === option.value ? styles.selectedItem : ''}`}
            onClick={() => handleSelect(option)}
        >
            {isCountry && (option.flag_url || option.code) && (
                <img
                    src={option.flag_url || getFlagUrl(option.code)}
                    alt={option.label}
                    className={styles.flagIcon}
                    loading="lazy"
                />
            )}
            <span className={styles.optionLabel}>{option.label}</span>
            {isCountry && option.subregion && (
                <span className={styles.subregionBadge}>{option.subregion}</span>
            )}
        </div>
    );

    return (
        <div className={styles.container} ref={containerRef}>
            {label && (
                <label className={styles.label}>
                    {label}{required && <span className={styles.required}> *</span>}
                </label>
            )}

            {/* ── Trigger ── */}
            <div
                className={`${styles.selectTrigger} ${isOpen ? styles.active : ''} ${disabled ? styles.disabled : ''} ${error ? styles.error : ''}`}
                onClick={() => !disabled && setIsOpen((o) => !o)}
                role="combobox"
                aria-expanded={isOpen}
                aria-haspopup="listbox"
                tabIndex={disabled ? -1 : 0}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); !disabled && setIsOpen((o) => !o); }
                    if (e.key === 'Escape') setIsOpen(false);
                }}
            >
                <div className={styles.selectedValueContainer}>
                    {selectedOption ? (
                        <div className={styles.optionContent}>
                            {isCountry && (selectedOption.flag_url || selectedOption.code) && (
                                <img
                                    src={selectedOption.flag_url || getFlagUrl(selectedOption.code)}
                                    alt={selectedOption.label}
                                    className={styles.flagIcon}
                                />
                            )}
                            <span className={styles.selectedLabel}>{selectedOption.label}</span>
                            {isCountry && selectedOption.region && (
                                <span className={styles.triggerRegionBadge}>{selectedOption.region}</span>
                            )}
                        </div>
                    ) : (
                        <span className={styles.placeholder}>{placeholder}</span>
                    )}
                </div>
                <div className={`${styles.arrowIcon} ${isOpen ? styles.arrowOpen : ''}`}>
                    <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
                        <path d="M5 7L10 12L15 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </div>
            </div>

            {/* ── Dropdown ── */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -8, scale: 0.98 }}
                        animate={{ opacity: 1, y: 0,  scale: 1    }}
                        exit={{    opacity: 0, y: -8, scale: 0.98 }}
                        transition={{ duration: 0.15, ease: 'easeOut' }}
                        className={styles.dropdown}
                        role="listbox"
                    >
                        {/* Search bar */}
                        <div className={styles.searchWrapper}>
                            <div className={styles.searchIcon}>
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
                                </svg>
                            </div>
                            <input
                                ref={inputRef}
                                className={styles.searchInput}
                                placeholder={isCountry ? 'Search country, region…' : 'Search…'}
                                value={searchTerm}
                                onChange={(e) => setSearch(e.target.value)}
                                aria-label="Search"
                            />
                            {searchTerm && (
                                <button
                                    className={styles.clearSearch}
                                    onClick={() => setSearch('')}
                                    aria-label="Clear search"
                                >✕</button>
                            )}
                        </div>

                        {/* Results count when searching */}
                        {searchTerm && filteredOptions.length > 0 && (
                            <div className={styles.resultCount}>
                                {filteredOptions.length} result{filteredOptions.length !== 1 ? 's' : ''}
                            </div>
                        )}

                        {/* Options list */}
                        <div className={styles.optionsList} ref={listRef}>
                            {options.length === 0 ? (
                                <div className={styles.noResults}>
                                    <div className={styles.noResultsTitle}>Loading countries…</div>
                                    <div className={styles.noResultsSub}>Connecting to geography data.</div>
                                </div>
                            ) : filteredOptions.length === 0 ? (
                                <div className={styles.noResults}>
                                    No matches for &ldquo;{searchTerm}&rdquo;
                                </div>
                            ) : grouped ? (
                                // Grouped by region
                                grouped.map(([region, items]) => (
                                    <div key={region} className={styles.regionGroup}>
                                        <div className={styles.regionGroupHeader}>
                                            <span className={styles.regionGroupDot} />
                                            {region}
                                            <span className={styles.regionGroupCount}>{items.length}</span>
                                        </div>
                                        {items.map(renderOption)}
                                    </div>
                                ))
                            ) : (
                                // Flat (searching)
                                filteredOptions.map(renderOption)
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {error && <span className={styles.errorMessage}>{error}</span>}
        </div>
    );
};

export default SearchableSelect;
