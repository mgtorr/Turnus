import React from 'react';
import * as Toast from '@radix-ui/react-toast';
import { cn } from '../../lib/utils';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface ToastMessage {
    id: string;
    message: string;
    type: ToastType;
    duration?: number;
}

interface GlassToastProps {
    toasts: ToastMessage[];
    onRemove: (id: string) => void;
}

interface ToastItemProps {
    toast: ToastMessage;
    onRemove: (id: string) => void;
}

const typeConfig = {
    success: {
        bg: 'from-emerald-500/90 to-teal-500/90',
        border: 'border-emerald-400/50',
        icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
        ),
    },
    error: {
        bg: 'from-red-500/90 to-rose-500/90',
        border: 'border-red-400/50',
        icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
        ),
    },
    info: {
        bg: 'from-cyan-500/90 to-blue-500/90',
        border: 'border-cyan-400/50',
        icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
    },
    warning: {
        bg: 'from-amber-500/90 to-orange-500/90',
        border: 'border-amber-400/50',
        icon: (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
        ),
    },
};

const ToastItem: React.FC<ToastItemProps> = ({ toast, onRemove }) => {
    const config = typeConfig[toast.type];

    return (
        <Toast.Root
            className={cn(
                'relative flex items-center gap-4',
                'px-6 py-4 rounded-2xl',
                'bg-gradient-to-r backdrop-blur-xl',
                config.bg,
                'border',
                config.border,
                'shadow-2xl',
                'text-white',
                // Animation
                'data-[state=open]:animate-fade-in-up',
                'data-[state=closed]:animate-fade-out',
                'data-[swipe=move]:translate-x-[var(--radix-toast-swipe-move-x)]',
                'data-[swipe=cancel]:translate-x-0 data-[swipe=cancel]:transition-transform',
                'data-[swipe=end]:translate-x-[var(--radix-toast-swipe-end-x)]'
            )}
            duration={toast.duration || 3000}
            onOpenChange={(open) => {
                if (!open) onRemove(toast.id);
            }}
        >
            <div className="p-2 rounded-full bg-white/20">
                {config.icon}
            </div>
            <Toast.Description className="flex-1 text-sm font-medium">
                {toast.message}
            </Toast.Description>
            <Toast.Close
                className={cn(
                    'p-1.5 rounded-full',
                    'hover:bg-white/20',
                    'transition-colors'
                )}
            >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
            </Toast.Close>
        </Toast.Root>
    );
};

const GlassToast: React.FC<GlassToastProps> = ({ toasts, onRemove }) => {
    return (
        <Toast.Provider swipeDirection="right">
            {toasts.map((toast) => (
                <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
            ))}
            <Toast.Viewport
                className={cn(
                    'fixed top-4 right-4 z-[100]',
                    'flex flex-col gap-3',
                    'w-[400px] max-w-[calc(100vw-2rem)]',
                    'outline-none'
                )}
            />
        </Toast.Provider>
    );
};

export default GlassToast;
