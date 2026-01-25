import React, { forwardRef } from 'react';
import { cn } from '../../lib/utils';

interface GlassInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    icon?: React.ReactNode;
    iconPosition?: 'left' | 'right';
}

const GlassInput = forwardRef<HTMLInputElement, GlassInputProps>(
    ({ className, label, error, icon, iconPosition = 'left', type = 'text', ...props }, ref) => {
        return (
            <div className="w-full">
                {label && (
                    <label className="block text-sm font-bold text-cyan-100 uppercase tracking-wider mb-2 ml-1">
                        {label}
                    </label>
                )}
                <div className="relative">
                    {icon && iconPosition === 'left' && (
                        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-[#64748b]">
                            {icon}
                        </div>
                    )}
                    <input
                        ref={ref}
                        type={type}
                        className={cn(
                            // Base styles
                            'w-full',
                            'bg-[rgba(14,36,64,0.6)]',
                            'backdrop-blur-xl',
                            'border border-[rgba(56,189,248,0.15)]',
                            'rounded-xl',
                            'text-[#f0f9ff]',
                            'placeholder-[#64748b]',
                            'transition-all duration-200',
                            // Padding based on icon
                            icon && iconPosition === 'left' ? 'pl-12 pr-4' : 'px-4',
                            icon && iconPosition === 'right' ? 'pr-12 pl-4' : '',
                            'py-4',
                            // Focus state
                            'focus:outline-none',
                            'focus:border-cyan-500',
                            'focus:ring-2 focus:ring-cyan-500/20',
                            // Error state
                            error && 'border-red-500 focus:border-red-500 focus:ring-red-500/20',
                            className
                        )}
                        {...props}
                    />
                    {icon && iconPosition === 'right' && (
                        <div className="absolute right-4 top-1/2 -translate-y-1/2 text-[#64748b]">
                            {icon}
                        </div>
                    )}
                </div>
                {error && (
                    <p className="mt-2 text-sm text-red-400 ml-1">{error}</p>
                )}
            </div>
        );
    }
);

GlassInput.displayName = 'GlassInput';

export default GlassInput;
