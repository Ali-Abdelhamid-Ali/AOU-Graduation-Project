import React from 'react';
import { Skeleton } from '../Skeleton';

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

export default SkeletonText;
