import React from 'react';
import { cn } from '../../lib/utils';

interface SpinnerProps {
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

const Spinner: React.FC<SpinnerProps> = ({ size = 'md', className }) => {
    const sizeClasses = {
        sm: 'w-6 h-6 border-2',
        md: 'w-12 h-12 border-3',
        lg: 'w-16 h-16 border-4',
    };

    return (
        <div className={cn('relative', className)}>
            {/* Outer ring */}
            <div
                className={cn(
                    'rounded-full animate-spin',
                    'border-cyan-500/20 border-t-cyan-500',
                    sizeClasses[size]
                )}
            />
            {/* Inner glow ring */}
            <div
                className={cn(
                    'absolute inset-0 rounded-full animate-spin-slow',
                    'border-transparent border-r-teal-500/50',
                    sizeClasses[size]
                )}
                style={{ animationDirection: 'reverse' }}
            />
        </div>
    );
};

export default Spinner;
