import { useState, useCallback } from 'react';
import type { ToastMessage, ToastType } from '../components/ui/GlassToast';

export const useToast = () => {
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    const addToast = useCallback((message: string, type: ToastType = 'info', duration: number = 3000) => {
        const id = Date.now().toString() + Math.random().toString(36);
        setToasts((prev) => [...prev, { id, message, type, duration }]);
    }, []);

    const removeToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
    }, []);

    const showSuccess = useCallback((message: string, duration?: number) => {
        addToast(message, 'success', duration);
    }, [addToast]);

    const showError = useCallback((message: string, duration?: number) => {
        addToast(message, 'error', duration);
    }, [addToast]);

    const showInfo = useCallback((message: string, duration?: number) => {
        addToast(message, 'info', duration);
    }, [addToast]);

    const showWarning = useCallback((message: string, duration?: number) => {
        addToast(message, 'warning', duration);
    }, [addToast]);

    return {
        toasts,
        removeToast,
        showSuccess,
        showError,
        showInfo,
        showWarning,
    };
};
