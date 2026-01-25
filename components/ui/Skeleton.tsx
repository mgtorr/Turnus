import React from 'react';
import { cn } from '../../lib/utils';

interface SkeletonProps {
    className?: string;
    variant?: 'default' | 'circular' | 'rounded';
    width?: string | number;
    height?: string | number;
    style?: React.CSSProperties;
}

const Skeleton: React.FC<SkeletonProps> = ({
    className,
    variant = 'default',
    width,
    height,
    style,
}) => {
    const variantClasses = {
        default: 'rounded-lg',
        circular: 'rounded-full',
        rounded: 'rounded-2xl',
    };

    return (
        <div
            className={cn(
                'relative overflow-hidden',
                'bg-[rgba(14,36,64,0.5)]',
                variantClasses[variant],
                // Shimmer effect
                'before:absolute before:inset-0',
                'before:bg-gradient-to-r',
                'before:from-transparent before:via-[rgba(56,189,248,0.1)] before:to-transparent',
                'before:animate-[shimmer_2s_infinite]',
                className
            )}
            style={{
                width: width,
                height: height,
                ...style
            }}
        />
    );
};

// Preset skeleton components
const SkeletonText: React.FC<{ lines?: number; className?: string }> = ({
    lines = 3,
    className
}) => (
    <div className={cn('space-y-3', className)}>
        {Array.from({ length: lines }).map((_, i) => (
            <Skeleton
                key={i}
                className="h-4"
                style={{ width: i === lines - 1 ? '70%' : '100%' }}
            />
        ))}
    </div>
);

const SkeletonCard: React.FC<{ className?: string }> = ({ className }) => (
    <div
        className={cn(
            'p-6 rounded-3xl',
            'bg-gradient-to-br from-[rgba(14,36,64,0.7)] to-[rgba(14,36,64,0.4)]',
            'border border-[rgba(56,189,248,0.1)]',
            className
        )}
    >
        <div className="flex items-center gap-4 mb-4">
            <Skeleton variant="circular" width={48} height={48} />
            <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
            </div>
        </div>
        <SkeletonText lines={3} />
    </div>
);

const SkeletonAvatar: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'md' }) => {
    const sizeMap = {
        sm: 32,
        md: 48,
        lg: 64,
    };
    return <Skeleton variant="circular" width={sizeMap[size]} height={sizeMap[size]} />;
};

export { Skeleton, SkeletonText, SkeletonCard, SkeletonAvatar };
export default Skeleton;
