import React from 'react';
import { cn } from '../../lib/utils';

interface BadgeProps {
    children: React.ReactNode;
    variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'gold' | 'locked';
    size?: 'sm' | 'md' | 'lg';
    icon?: React.ReactNode;
    className?: string;
    pulse?: boolean;
}

const Badge: React.FC<BadgeProps> = ({
    children,
    variant = 'default',
    size = 'md',
    icon,
    className,
    pulse = false,
}) => {
    const sizeClasses = {
        sm: 'px-2 py-0.5 text-xs',
        md: 'px-3 py-1 text-sm',
        lg: 'px-4 py-1.5 text-base',
    };

    const variantClasses = {
        default: [
            'bg-[rgba(14,36,64,0.6)]',
            'border-[rgba(56,189,248,0.2)]',
            'text-[#f0f9ff]',
        ],
        success: [
            'bg-emerald-500/20',
            'border-emerald-500/30',
            'text-emerald-400',
        ],
        warning: [
            'bg-amber-500/20',
            'border-amber-500/30',
            'text-amber-400',
        ],
        error: [
            'bg-red-500/20',
            'border-red-500/30',
            'text-red-400',
        ],
        info: [
            'bg-cyan-500/20',
            'border-cyan-500/30',
            'text-cyan-400',
        ],
        gold: [
            'bg-gradient-to-r from-amber-500/20 to-orange-500/20',
            'border-amber-500/30',
            'text-amber-400',
        ],
        locked: [
            'bg-[rgba(14,36,64,0.4)]',
            'border-[rgba(56,189,248,0.1)]',
            'text-[#64748b]',
            'opacity-60',
        ],
    };

    return (
        <span
            className={cn(
                'inline-flex items-center gap-1.5',
                'rounded-full',
                'border',
                'font-semibold',
                'backdrop-blur-sm',
                sizeClasses[size],
                variantClasses[variant],
                pulse && 'animate-pulse',
                className
            )}
        >
            {icon && <span className="shrink-0">{icon}</span>}
            {children}
        </span>
    );
};

export default Badge;
