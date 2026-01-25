import React from 'react';
import { cn } from '../../lib/utils';

interface GlassButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children: React.ReactNode;
    variant?: 'default' | 'primary' | 'secondary' | 'ghost' | 'danger' | 'gold';
    size?: 'sm' | 'md' | 'lg';
    loading?: boolean;
    icon?: React.ReactNode;
    iconPosition?: 'left' | 'right';
}

const GlassButton: React.FC<GlassButtonProps> = ({
    children,
    className,
    variant = 'default',
    size = 'md',
    loading = false,
    icon,
    iconPosition = 'left',
    disabled,
    ...props
}) => {
    const sizeClasses = {
        sm: 'px-4 py-2 text-sm rounded-lg',
        md: 'px-6 py-3 text-base rounded-xl',
        lg: 'px-8 py-4 text-lg rounded-2xl',
    };

    const variantClasses = {
        default: [
            'bg-gradient-to-br from-[rgba(14,36,64,0.8)] to-[rgba(14,36,64,0.5)]',
            'backdrop-blur-xl',
            'border border-[rgba(56,189,248,0.15)]',
            'text-[#f0f9ff]',
            'hover:border-[rgba(6,182,212,0.4)]',
            'hover:shadow-lg hover:shadow-cyan-500/20',
        ],
        primary: [
            'bg-gradient-to-r from-cyan-500 to-teal-500',
            'border-none',
            'text-white',
            'shadow-lg shadow-cyan-500/30',
            'hover:shadow-xl hover:shadow-cyan-500/40',
        ],
        secondary: [
            'bg-gradient-to-r from-violet-500 to-purple-500',
            'border-none',
            'text-white',
            'shadow-lg shadow-violet-500/30',
            'hover:shadow-xl hover:shadow-violet-500/40',
        ],
        ghost: [
            'bg-transparent',
            'border border-transparent',
            'text-[#94a3b8]',
            'hover:bg-[rgba(14,36,64,0.4)]',
            'hover:text-[#f0f9ff]',
            'hover:border-[rgba(56,189,248,0.15)]',
        ],
        danger: [
            'bg-gradient-to-r from-red-500 to-rose-500',
            'border-none',
            'text-white',
            'shadow-lg shadow-red-500/30',
            'hover:shadow-xl hover:shadow-red-500/40',
        ],
        gold: [
            'bg-gradient-to-r from-amber-500 to-orange-500',
            'border-none',
            'text-white',
            'shadow-lg shadow-amber-500/30',
            'hover:shadow-xl hover:shadow-amber-500/40',
        ],
    };

    return (
        <button
            className={cn(
                // Base styles
                'relative font-semibold',
                'transition-all duration-200 ease-out',
                'transform active:scale-[0.98]',
                'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none',
                'flex items-center justify-center gap-2',
                // Focus ring
                'focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:ring-offset-2 focus:ring-offset-[#030712]',
                // Size
                sizeClasses[size],
                // Variant
                variantClasses[variant],
                // Hover lift
                !disabled && 'hover:-translate-y-0.5',
                className
            )}
            disabled={disabled || loading}
            {...props}
        >
            {loading ? (
                <>
                    <svg
                        className="animate-spin h-5 w-5"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                    >
                        <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                        />
                        <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                    </svg>
                    <span>Loading...</span>
                </>
            ) : (
                <>
                    {icon && iconPosition === 'left' && icon}
                    {children}
                    {icon && iconPosition === 'right' && icon}
                </>
            )}
        </button>
    );
};

export default GlassButton;
