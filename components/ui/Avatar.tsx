import React from 'react';
import * as AvatarPrimitive from '@radix-ui/react-avatar';
import { cn } from '../../lib/utils';

interface AvatarProps {
    src?: string;
    alt?: string;
    fallback: string;
    size?: 'sm' | 'md' | 'lg' | 'xl';
    className?: string;
    ring?: boolean;
    ringColor?: 'cyan' | 'gold' | 'violet' | 'emerald';
}

const Avatar: React.FC<AvatarProps> = ({
    src,
    alt,
    fallback,
    size = 'md',
    className,
    ring = false,
    ringColor = 'cyan',
}) => {
    const sizeClasses = {
        sm: 'w-8 h-8 text-xs',
        md: 'w-12 h-12 text-sm',
        lg: 'w-16 h-16 text-lg',
        xl: 'w-24 h-24 text-2xl',
    };

    const ringClasses = {
        cyan: 'ring-cyan-500 shadow-cyan-500/30',
        gold: 'ring-amber-500 shadow-amber-500/30',
        violet: 'ring-violet-500 shadow-violet-500/30',
        emerald: 'ring-emerald-500 shadow-emerald-500/30',
    };

    return (
        <AvatarPrimitive.Root
            className={cn(
                'relative inline-flex items-center justify-center overflow-hidden rounded-full',
                'bg-gradient-to-br from-[rgba(14,36,64,0.8)] to-[rgba(14,36,64,0.5)]',
                'border border-[rgba(56,189,248,0.2)]',
                ring && [
                    'ring-4',
                    ringClasses[ringColor],
                    'shadow-lg',
                ],
                sizeClasses[size],
                className
            )}
        >
            <AvatarPrimitive.Image
                src={src}
                alt={alt}
                className="w-full h-full object-cover"
            />
            <AvatarPrimitive.Fallback
                className={cn(
                    'flex items-center justify-center w-full h-full',
                    'bg-gradient-to-br from-cyan-500 to-teal-500',
                    'text-white font-bold uppercase'
                )}
                delayMs={600}
            >
                {fallback.slice(0, 2)}
            </AvatarPrimitive.Fallback>
        </AvatarPrimitive.Root>
    );
};

export default Avatar;
