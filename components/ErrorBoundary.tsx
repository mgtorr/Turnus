import React, { Component, ErrorInfo, ReactNode } from 'react';
import GlassCard from './ui/GlassCard';
import GlassButton from './ui/GlassButton';
import Background from './layout/Background';

interface Props {
    children?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null,
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    private handleReload = () => {
        window.location.reload();
    };

    public render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center p-4">
                    <Background />
                    <GlassCard className="max-w-md text-center">
                        <h1 className="text-3xl font-black text-[#f0f9ff] mb-4">Something went wrong</h1>
                        <p className="text-[#94a3b8] mb-6">
                            We encountered an unexpected error. Please try reloading the page.
                        </p>
                        {this.state.error && (
                            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mb-6 text-left overflow-auto max-h-32">
                                <code className="text-xs text-red-300 font-mono">
                                    {this.state.error.toString()}
                                </code>
                            </div>
                        )}
                        <GlassButton variant="primary" onClick={this.handleReload}>
                            Reload Page
                        </GlassButton>
                    </GlassCard>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
