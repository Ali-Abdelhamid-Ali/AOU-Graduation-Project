import React from 'react';

/**
 * 🦴 Skeleton Component
 * A reusable placeholder for loading states with a smooth pulse animation.
 * @param {string} width - Width of the skeleton (e.g., '100%', '200px').
 * @param {string} height - Height of the skeleton.
 * @param {string} borderRadius - Border radius (e.g., 'svg', '10px', '50%').
 * @param {string} className - Optional additional class names.
 * @param {Object} style - Optional inline styles.
 */
export const Skeleton = ({
    width = '100%',
    height = '200px',
    borderRadius = '12px',
    className = '',
    style = {}
}) => {
    return (
        <div
            className={`skeleton ${className}`}
            style={{
                width,
                height,
                borderRadius,
                ...style
            }}
        />
    );
};

export const SkeletonText = ({ lines = 1, width = '100%' }) => {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', width }}>
            {Array.from({ length: lines }).map((_, i) => (
                <Skeleton
                    key={i}
                    height="1rem"
                    width={i === lines - 1 && lines > 1 ? '70%' : '100%'}
                    borderRadius="4px"
                />
            ))}
        </div>
    );
};

export const SkeletonCircle = ({ size = '48px' }) => {
    return (
        <Skeleton
            width={size}
            height={size}
            borderRadius="50%"
        />
    );
};
