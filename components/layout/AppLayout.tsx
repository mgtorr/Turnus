import React, { useState } from 'react';
import { cn } from '../../lib/utils';
import Background from './Background';
import GlassTooltip from '../ui/GlassTooltip';
import Avatar from '../ui/Avatar';

type View = 'dashboard' | 'calendar' | 'tutor' | 'profile' | 'vocabulary';

interface NavItem {
    view: View;
    label: string;
    icon: React.ReactNode;
}

interface AppLayoutProps {
    children: React.ReactNode;
    activeView: View;
    onViewChange: (view: View) => void;
    userName?: string;
    userLanguage?: string;
    userLevel?: string;
}

const navItems: NavItem[] = [
    {
        view: 'dashboard',
        label: 'Dashboard',
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" />
            </svg>
        ),
    },
    {
        view: 'calendar',
        label: 'Calendar',
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20a2 2 0 002 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM9 14H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2zm-8 4H7v-2h2v2zm4 0h-2v-2h2v2zm4 0h-2v-2h2v2z" />
            </svg>
        ),
    },
    {
        view: 'tutor',
        label: 'AI Tutor',
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z" />
            </svg>
        ),
    },
    {
        view: 'vocabulary',
        label: 'Vocabulary',
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9h-4v4h-2v-4H9V9h4V5h2v4h4v2z" />
            </svg>
        ),
    },
    {
        view: 'profile',
        label: 'Profile',
        icon: (
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
            </svg>
        ),
    },
];

const Logo: React.FC<{ className?: string }> = ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" className={className} fill="none">
        <defs>
            <linearGradient id="logoGradientNew" x1="10" y1="10" x2="90" y2="90" gradientUnits="userSpaceOnUse">
                <stop stopColor="#06b6d4" />
                <stop offset="1" stopColor="#14b8a6" />
            </linearGradient>
        </defs>
        <path
            d="M20 50C20 33.4315 33.4315 20 50 20C66.5685 20 80 33.4315 80 50C80 60 75 69 67 74L65 85L55 80C53.3 80.2 51.7 80.2 50 80.2C33.4 80.2 20 66.8 20 50Z"
            fill="url(#logoGradientNew)"
            fillOpacity="0.15"
        />
        <path
            d="M35 50C35 50 42 42 50 42C58 42 65 50 65 50"
            stroke="url(#logoGradientNew)"
            strokeWidth="6"
            strokeLinecap="round"
            strokeLinejoin="round"
        />
        <path
            d="M35 50C35 50 42 58 50 58C58 58 65 50 65 50"
            stroke="url(#logoGradientNew)"
            strokeWidth="6"
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity="0.7"
        />
        <circle cx="72" cy="28" r="4" fill="#06b6d4" />
    </svg>
);

const AppLayout: React.FC<AppLayoutProps> = ({
    children,
    activeView,
    onViewChange,
    userName = 'User',
    userLanguage,
    userLevel,
}) => {
    const [sidebarExpanded, setSidebarExpanded] = useState(true);

    return (
        <div className="flex min-h-screen text-[#f0f9ff]">
            <Background />

            {/* Sidebar */}
            <aside
                className={cn(
                    'fixed left-4 top-4 bottom-4 z-40',
                    'flex flex-col',
                    'transition-all duration-300 ease-out',
                    // Glass effect
                    'bg-gradient-to-br from-[rgba(14,36,64,0.8)] to-[rgba(14,36,64,0.5)]',
                    'backdrop-blur-2xl',
                    'border border-[rgba(56,189,248,0.15)]',
                    'rounded-3xl',
                    'shadow-2xl shadow-black/30',
                    // Width
                    sidebarExpanded ? 'w-72' : 'w-20'
                )}
                onMouseEnter={() => setSidebarExpanded(true)}
                onMouseLeave={() => setSidebarExpanded(false)}
            >
                {/* Logo */}
                <div className="h-20 flex items-center justify-center px-4 shrink-0">
                    <div className="flex items-center gap-3">
                        <Logo className="w-10 h-10 shrink-0" />
                        <span
                            className={cn(
                                'text-xl font-black text-gradient whitespace-nowrap',
                                'transition-all duration-300',
                                sidebarExpanded ? 'opacity-100 w-auto' : 'opacity-0 w-0 overflow-hidden'
                            )}
                        >
                            FluentFlow
                        </span>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-3 py-4 space-y-2">
                    {navItems.map((item) => (
                        <GlassTooltip
                            key={item.view}
                            content={item.label}
                            side="right"
                            delayDuration={sidebarExpanded ? 1000 : 100}
                        >
                            <button
                                onClick={() => onViewChange(item.view)}
                                className={cn(
                                    'group w-full flex items-center gap-4',
                                    'h-14 px-4 rounded-2xl',
                                    'transition-all duration-200',
                                    activeView === item.view
                                        ? [
                                            'bg-gradient-to-r from-cyan-500 to-teal-500',
                                            'text-white',
                                            'shadow-lg shadow-cyan-500/30',
                                        ]
                                        : [
                                            'text-[#94a3b8]',
                                            'hover:bg-[rgba(14,36,64,0.5)]',
                                            'hover:text-cyan-400',
                                        ]
                                )}
                            >
                                <span
                                    className={cn(
                                        'shrink-0 transition-transform duration-200',
                                        'group-hover:scale-110',
                                        activeView === item.view && 'animate-pulse-slow'
                                    )}
                                >
                                    {item.icon}
                                </span>
                                <span
                                    className={cn(
                                        'font-semibold whitespace-nowrap',
                                        'transition-all duration-300',
                                        sidebarExpanded ? 'opacity-100' : 'opacity-0 w-0 overflow-hidden'
                                    )}
                                >
                                    {item.label}
                                </span>
                            </button>
                        </GlassTooltip>
                    ))}
                </nav>

                {/* User Info */}
                <div
                    className={cn(
                        'px-4 pb-4 shrink-0',
                        'transition-all duration-300',
                        sidebarExpanded ? 'opacity-100' : 'opacity-0'
                    )}
                >
                    <div className="p-4 rounded-2xl bg-[rgba(14,36,64,0.5)] border border-[rgba(56,189,248,0.1)]">
                        <div className="flex items-center gap-3 mb-3">
                            <Avatar fallback={userName} size="sm" ring ringColor="cyan" />
                            <div className="min-w-0">
                                <p className="font-semibold text-[#f0f9ff] truncate">{userName}</p>
                            </div>
                        </div>
                        {userLanguage && userLevel && (
                            <div className="text-xs text-[#64748b] uppercase tracking-wider">
                                <span className="text-cyan-400">{userLanguage}</span>
                                <span className="mx-1">•</span>
                                <span>{userLevel}</span>
                            </div>
                        )}
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main
                className={cn(
                    'flex-1 min-h-screen',
                    'transition-all duration-300',
                    sidebarExpanded ? 'ml-80' : 'ml-28',
                    'p-6 lg:p-8'
                )}
            >
                <div className="max-w-7xl mx-auto">
                    {children}
                </div>
            </main>

            {/* Mobile Bottom Navigation */}
            <nav
                className={cn(
                    'fixed bottom-4 left-4 right-4 z-40',
                    'lg:hidden',
                    'flex justify-around items-center',
                    'h-16 px-4 rounded-2xl',
                    'bg-gradient-to-r from-[rgba(14,36,64,0.95)] to-[rgba(14,36,64,0.85)]',
                    'backdrop-blur-2xl',
                    'border border-[rgba(56,189,248,0.15)]',
                    'shadow-2xl shadow-black/30'
                )}
            >
                {navItems.map((item) => (
                    <button
                        key={item.view}
                        onClick={() => onViewChange(item.view)}
                        className={cn(
                            'p-3 rounded-xl transition-all duration-200',
                            activeView === item.view
                                ? 'bg-gradient-to-r from-cyan-500 to-teal-500 text-white shadow-lg shadow-cyan-500/30'
                                : 'text-[#64748b] hover:text-cyan-400'
                        )}
                    >
                        {item.icon}
                    </button>
                ))}
            </nav>
        </div>
    );
};

export default AppLayout;
