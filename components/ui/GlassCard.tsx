import React from 'react';
import { cn } from '../../lib/utils';

interface GlassCardProps {
    children: React.ReactNode;
    className?: string;
    title?: string;
    subtitle?: string;
    variant?: 'default' | 'highlight' | 'gold' | 'gradient';
    hover?: boolean;
    padding?: 'none' | 'sm' | 'md' | 'lg';
}

const GlassCard: React.FC<GlassCardProps> = ({
    children,
    className,
    title,
    subtitle,
    variant = 'default',
    hover = true,
    padding = 'lg',
}) => {
    const paddingClasses = {
        none: '',
        sm: 'p-4',
        md: 'p-6',
        lg: 'p-8',
    };

    const variantClasses = {
        default: '',
        highlight: 'border-cyan-500/30 shadow-cyan-500/10',
        gold: 'border-amber-500/30 shadow-amber-500/10',
        gradient: 'bg-gradient-to-br from-cyan-500/10 to-teal-500/10',
    };

    return (
        <div
            className={cn(
                // Base glass styles
                'relative overflow-hidden rounded-3xl',
                'bg-gradient-to-br from-[rgba(14,36,64,0.7)] to-[rgba(14,36,64,0.4)]',
                'backdrop-blur-xl',
                'border border-[rgba(56,189,248,0.15)]',
                'shadow-xl shadow-black/20',
                // Top highlight line
                'before:absolute before:top-0 before:left-0 before:right-0 before:h-px',
                'before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent',
                // Hover effects
                hover && [
                    'transition-all duration-300',
                    'hover:border-[rgba(6,182,212,0.4)]',
                    'hover:shadow-2xl hover:shadow-cyan-500/10',
                    'hover:-translate-y-1',
                ],
                // Padding
                paddingClasses[padding],
                // Variant styles
                variantClasses[variant],
                className
            )}
        >
            {/* Decorative corner glow */}
            <div className="absolute top-0 right-0 -mt-10 -mr-10 w-40 h-40 bg-gradient-to-br from-cyan-500/10 to-teal-500/10 rounded-full blur-3xl pointer-events-none" />

            {/* Content */}
            <div className="relative z-10">
                {(title || subtitle) && (
                    <div className="mb-6">
                        {title && (
                            <h2 className="text-2xl font-bold text-[#f0f9ff]">
                                {title}
                            </h2>
                        )}
                        {subtitle && (
                            <p className="text-[#94a3b8] mt-1 text-sm">
                                {subtitle}
                            </p>
                        )}
                    </div>
                )}
                {children}
            </div>
        </div>
    );
};

export default GlassCard;
