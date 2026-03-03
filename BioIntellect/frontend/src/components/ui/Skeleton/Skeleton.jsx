import React from 'react';

/**
 * 🦴 Skeleton Component
 * A reusable placeholder for loading states with a smooth pulse animation.
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

export default Skeleton;
