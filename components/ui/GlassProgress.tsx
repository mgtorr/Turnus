import React from 'react';
import * as Progress from '@radix-ui/react-progress';
import { cn } from '../../lib/utils';

interface GlassProgressProps {
    value: number;
    max?: number;
    className?: string;
    variant?: 'default' | 'cyan' | 'teal' | 'gold' | 'violet';
    size?: 'sm' | 'md' | 'lg';
    showLabel?: boolean;
    label?: string;
    animated?: boolean;
}

const GlassProgress: React.FC<GlassProgressProps> = ({
    value,
    max = 100,
    className,
    variant = 'cyan',
    size = 'md',
    showLabel = false,
    label,
    animated = true,
}) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

    const sizeClasses = {
        sm: 'h-1.5',
        md: 'h-2.5',
        lg: 'h-4',
    };

    const variantClasses = {
        default: 'bg-gradient-to-r from-slate-500 to-slate-400',
        cyan: 'bg-gradient-to-r from-cyan-500 to-teal-500 shadow-[0_0_10px_rgba(6,182,212,0.5)]',
        teal: 'bg-gradient-to-r from-teal-500 to-emerald-500 shadow-[0_0_10px_rgba(20,184,166,0.5)]',
        gold: 'bg-gradient-to-r from-amber-500 to-orange-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]',
        violet: 'bg-gradient-to-r from-violet-500 to-purple-500 shadow-[0_0_10px_rgba(139,92,246,0.5)]',
    };

    return (
        <div className={cn('w-full', className)}>
            {(showLabel || label) && (
                <div className="flex justify-between items-center mb-2">
                    {label && (
                        <span className="text-sm font-medium text-[#f0f9ff]">{label}</span>
                    )}
                    {showLabel && (
                        <span className="text-sm font-bold text-[#94a3b8]">{Math.round(percentage)}%</span>
                    )}
                </div>
            )}
            <Progress.Root
                className={cn(
                    'relative overflow-hidden rounded-full',
                    'bg-[rgba(14,36,64,0.6)]',
                    'backdrop-blur-sm',
                    'border border-[rgba(56,189,248,0.1)]',
                    sizeClasses[size]
                )}
                value={value}
                max={max}
            >
                <Progress.Indicator
                    className={cn(
                        'h-full rounded-full',
                        animated && 'transition-all duration-700 ease-out',
                        variantClasses[variant]
                    )}
                    style={{ width: `${percentage}%` }}
                />
            </Progress.Root>
        </div>
    );
};

export default GlassProgress;
