import React from 'react';
import { cn } from '../../lib/utils';

interface CardProps {
    children: React.ReactNode;
    className?: string;
    title?: string;
    subtitle?: string;
    hover?: boolean;
}

const Card: React.FC<CardProps> = ({ children, className, title, subtitle, hover = true }) => {
    return (
        <div className={cn(
            'relative overflow-hidden',
            // Glass effect
            'bg-gradient-to-br from-[rgba(14,36,64,0.7)] to-[rgba(14,36,64,0.4)]',
            'backdrop-blur-xl',
            'border border-[rgba(56,189,248,0.15)]',
            'rounded-3xl',
            'shadow-xl shadow-black/20',
            'p-8',
            // Hover effects
            hover && [
                'transition-all duration-300',
                'hover:border-[rgba(6,182,212,0.3)]',
                'hover:shadow-2xl hover:shadow-cyan-500/10',
                'hover:-translate-y-1'
            ],
            className
        )}>
            {/* Header */}
            {(title || subtitle) && (
                <div className="mb-6">
                    {title && (
                        <h2 className="text-2xl font-bold text-[#f0f9ff]">{title}</h2>
                    )}
                    {subtitle && (
                        <p className="text-sm text-[#94a3b8] mt-1">{subtitle}</p>
                    )}
                </div>
            )}
            {children}

            {/* Decorative Glow */}
            <div className="absolute top-0 right-0 -mt-10 -mr-10 w-40 h-40 bg-gradient-to-br from-cyan-500/10 to-teal-500/10 rounded-full blur-3xl pointer-events-none" />
        </div>
    );
};

export default Card;