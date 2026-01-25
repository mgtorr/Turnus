import React from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { cn } from '../../lib/utils';

interface GlassDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    children: React.ReactNode;
    title?: string;
    description?: string;
    className?: string;
}

interface GlassDialogTriggerProps {
    children: React.ReactNode;
    asChild?: boolean;
}

const GlassDialog: React.FC<GlassDialogProps> = ({
    open,
    onOpenChange,
    children,
    title,
    description,
    className,
}) => {
    return (
        <Dialog.Root open={open} onOpenChange={onOpenChange}>
            <Dialog.Portal>
                <Dialog.Overlay
                    className={cn(
                        'fixed inset-0 z-50',
                        'bg-[#030712]/80 backdrop-blur-md',
                        'data-[state=open]:animate-fade-in',
                        'data-[state=closed]:animate-fade-out'
                    )}
                />
                <Dialog.Content
                    className={cn(
                        'fixed z-50',
                        'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2',
                        'w-full max-w-2xl max-h-[90vh]',
                        'overflow-hidden',
                        // Glass effect
                        'bg-gradient-to-br from-[rgba(14,36,64,0.9)] to-[rgba(14,36,64,0.7)]',
                        'backdrop-blur-2xl',
                        'border border-[rgba(56,189,248,0.2)]',
                        'rounded-3xl',
                        'shadow-2xl shadow-black/50',
                        // Top highlight
                        'before:absolute before:top-0 before:left-0 before:right-0 before:h-px',
                        'before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent',
                        // Animation
                        'data-[state=open]:animate-fade-in-up',
                        'data-[state=closed]:animate-fade-out',
                        // Focus
                        'focus:outline-none',
                        className
                    )}
                >
                    {/* Close button */}
                    <Dialog.Close
                        className={cn(
                            'absolute top-6 right-6 z-10',
                            'p-2 rounded-full',
                            'bg-[rgba(14,36,64,0.5)]',
                            'border border-[rgba(56,189,248,0.15)]',
                            'text-[#94a3b8] hover:text-[#f0f9ff]',
                            'transition-all duration-200',
                            'hover:bg-[rgba(14,36,64,0.8)]',
                            'focus:outline-none focus:ring-2 focus:ring-cyan-500/50'
                        )}
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </Dialog.Close>

                    {/* Header */}
                    {(title || description) && (
                        <div className="p-8 pb-0">
                            {title && (
                                <Dialog.Title className="text-2xl font-bold text-[#f0f9ff] mb-2">
                                    {title}
                                </Dialog.Title>
                            )}
                            {description && (
                                <Dialog.Description className="text-[#94a3b8]">
                                    {description}
                                </Dialog.Description>
                            )}
                        </div>
                    )}

                    {/* Content */}
                    <div className="p-8 overflow-y-auto max-h-[calc(90vh-8rem)] custom-scrollbar">
                        {children}
                    </div>
                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
};

const GlassDialogTrigger: React.FC<GlassDialogTriggerProps> = ({ children, asChild }) => {
    return (
        <Dialog.Trigger asChild={asChild}>
            {children}
        </Dialog.Trigger>
    );
};

export { GlassDialog, GlassDialogTrigger };
export default GlassDialog;
