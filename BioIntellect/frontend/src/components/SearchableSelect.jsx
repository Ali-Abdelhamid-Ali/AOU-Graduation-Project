import React, { useState, useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styles from './SearchableSelect.module.css';

/**
 * SearchableSelect
 * A premium, high-performance searchable dropdown component.
 * Features:
 * - Searchable options
 * - Flag support (via flagcdn)
 * - Accessibility (click outside, keyboard nav)
 * - Optimized for large datasets
 */
const SearchableSelect = ({
    label,
    value,
    onChange,
    options = [],
    required = false,
    disabled = false,
    placeholder = "Select an option...",
    isCountry = false,
    error = null
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const containerRef = useRef(null);
    const inputRef = useRef(null);

    // Filter options based on search term
    const filteredOptions = useMemo(() => {
        if (!searchTerm) return options;
        const lowerSearch = searchTerm.toLowerCase();
        return options.filter(opt =>
            opt.label.toLowerCase().includes(lowerSearch) ||
            (opt.code && opt.code.toLowerCase().includes(lowerSearch))
        );
    }, [options, searchTerm]);

    // Handle outside clicks
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (containerRef.current && !containerRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const selectedOption = useMemo(() =>
        options.find(opt => opt.value === value),
        [options, value]
    );

    const handleSelect = (option) => {
        onChange({ target: { value: option.value, name: label } });
        setIsOpen(false);
        setSearchTerm("");
    };

    const getFlagUrl = (code) => {
        if (!code) return null;
        return `https://flagcdn.com/w40/${code.toLowerCase()}.png`;
    };

    return (
        <div className={styles.container} ref={containerRef}>
            {label && (
                <label className={styles.label}>
                    {label} {required && <span className={styles.required}>*</span>}
                </label>
            )}

            <div
                className={`${styles.selectTrigger} ${isOpen ? styles.active : ''} ${disabled ? styles.disabled : ''} ${error ? styles.error : ''}`}
                onClick={() => !disabled && setIsOpen(!isOpen)}
            >
                <div className={styles.selectedValueContainer}>
                    {selectedOption ? (
                        <div className={styles.optionContent}>
                            {isCountry && (selectedOption.flag_url || selectedOption.code) && (
                                <img
                                    src={selectedOption.flag_url || getFlagUrl(selectedOption.code)}
                                    alt={selectedOption.code || selectedOption.label}
                                    className={styles.flagIcon}
                                />
                            )}
                            <span className={styles.selectedLabel}>{selectedOption.label}</span>
                        </div>
                    ) : (
                        <span className={styles.placeholder}>{placeholder}</span>
                    )}
                </div>
                <div className={styles.arrowIcon}>
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path d="M5 7L10 12L15 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </div>
            </div>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className={styles.dropdown}
                    >
                        <div className={styles.searchWrapper}>
                            <div className={styles.searchIcon}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
                                </svg>
                            </div>
                            <input
                                ref={inputRef}
                                autoFocus
                                className={styles.searchInput}
                                placeholder="Search..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                            />
                        </div>

                        <div className={styles.optionsList}>
                            {options.length === 0 ? (
                                <div className={styles.noResults}>
                                    <div style={{ marginBottom: '0.4rem', fontWeight: 600 }}>Loading global geography...</div>
                                    <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>We are connecting to the clinical geography network.</div>
                                </div>
                            ) : filteredOptions.length > 0 ? (
                                filteredOptions.map((option) => (
                                    <div
                                        key={option.value}
                                        className={`${styles.optionItem} ${value === option.value ? styles.selectedItem : ''}`}
                                        onClick={() => handleSelect(option)}
                                    >
                                        {isCountry && (option.flag_url || option.code) && (
                                            <img
                                                src={option.flag_url || getFlagUrl(option.code)}
                                                alt={option.code || option.label}
                                                className={styles.flagIcon}
                                            />
                                        )}
                                        <span className={styles.optionLabel}>{option.label}</span>
                                    </div>
                                ))
                            ) : (
                                <div className={styles.noResults}>No matches found for "{searchTerm}"</div>
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
