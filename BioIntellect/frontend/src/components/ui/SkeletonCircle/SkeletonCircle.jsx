import React from 'react';
import { Skeleton } from '../Skeleton';

export const SkeletonCircle = ({ size = '48px' }) => {
    return (
        <Skeleton
            width={size}
            height={size}
            borderRadius="50%"
        />
    );
};

export default SkeletonCircle;
