import React, { useEffect, useState } from 'react';
import { cn } from '../../lib/utils';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface ToastMessage {
    id: string;
    message: string;
    type: ToastType;
    duration?: number;
}

interface ToastProps {
    toasts: ToastMessage[];
    onRemove: (id: string) => void;
}

const Toast: React.FC<ToastProps> = ({ toasts, onRemove }) => {
    return (
        <div className="fixed top-4 right-4 z-50 space-y-3 pointer-events-none">
            {toasts.map((toast) => (
                <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
            ))}
        </div>
    );
};

const ToastItem: React.FC<{ toast: ToastMessage; onRemove: (id: string) => void }> = ({ toast, onRemove }) => {
    const [isExiting, setIsExiting] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setIsExiting(true);
            setTimeout(() => onRemove(toast.id), 300);
        }, toast.duration || 4000);

        return () => clearTimeout(timer);
    }, [toast, onRemove]);

    const typeStyles = {
        success: {
            bg: 'bg-gradient-to-r from-emerald-500/20 to-teal-500/20',
            border: 'border-emerald-500/30',
            icon: 'bg-emerald-500/30 text-emerald-400',
            text: 'text-emerald-300',
        },
        error: {
            bg: 'bg-gradient-to-r from-red-500/20 to-rose-500/20',
            border: 'border-red-500/30',
            icon: 'bg-red-500/30 text-red-400',
            text: 'text-red-300',
        },
        info: {
            bg: 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20',
            border: 'border-cyan-500/30',
            icon: 'bg-cyan-500/30 text-cyan-400',
            text: 'text-cyan-300',
        },
        warning: {
            bg: 'bg-gradient-to-r from-amber-500/20 to-orange-500/20',
            border: 'border-amber-500/30',
            icon: 'bg-amber-500/30 text-amber-400',
            text: 'text-amber-300',
        },
    };

    const icons = {
        success: (
            <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
        ),
        error: (
            <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
        ),
        info: (
            <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
        ),
        warning: (
            <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
        ),
    };

    const style = typeStyles[toast.type];

    return (
        <div
            className={cn(
                'pointer-events-auto',
                'px-5 py-4 rounded-2xl',
                // Glass effect
                style.bg,
                'backdrop-blur-2xl',
                'border',
                style.border,
                'shadow-2xl shadow-black/30',
                // Animation
                'transform transition-all duration-300 ease-out',
                isExiting
                    ? 'translate-x-[400px] opacity-0'
                    : 'translate-x-0 opacity-100',
                'flex items-center gap-3 min-w-[320px] max-w-md'
            )}
        >
            <span className={cn(
                'p-2 rounded-xl shrink-0',
                style.icon
            )}>
                {icons[toast.type]}
            </span>
            <p className={cn('flex-1 font-medium text-[#f0f9ff]')}>{toast.message}</p>
            <button
                onClick={() => {
                    setIsExiting(true);
                    setTimeout(() => onRemove(toast.id), 300);
                }}
                className="text-[#64748b] hover:text-[#f0f9ff] transition-colors p-1 rounded-lg hover:bg-[rgba(255,255,255,0.1)]"
            >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    );
};

export default Toast;
