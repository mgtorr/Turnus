import React from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import { cn } from '../../lib/utils';

interface TabItem {
    value: string;
    label: string;
    icon?: React.ReactNode;
}

interface GlassTabsProps {
    tabs: TabItem[];
    defaultValue?: string;
    value?: string;
    onValueChange?: (value: string) => void;
    children: React.ReactNode;
    className?: string;
}

interface GlassTabContentProps {
    value: string;
    children: React.ReactNode;
    className?: string;
}

const GlassTabs: React.FC<GlassTabsProps> = ({
    tabs,
    defaultValue,
    value,
    onValueChange,
    children,
    className,
}) => {
    return (
        <Tabs.Root
            defaultValue={defaultValue || tabs[0]?.value}
            value={value}
            onValueChange={onValueChange}
            className={cn('w-full', className)}
        >
            <Tabs.List
                className={cn(
                    'flex p-1.5 rounded-xl',
                    'bg-[rgba(14,36,64,0.5)]',
                    'backdrop-blur-sm',
                    'border border-[rgba(56,189,248,0.1)]',
                    'mb-4'
                )}
            >
                {tabs.map((tab) => (
                    <Tabs.Trigger
                        key={tab.value}
                        value={tab.value}
                        className={cn(
                            'flex-1 flex items-center justify-center gap-2',
                            'px-4 py-2.5 rounded-lg',
                            'text-sm font-medium',
                            'transition-all duration-200',
                            'text-[#94a3b8]',
                            'hover:text-[#f0f9ff]',
                            // Active state
                            'data-[state=active]:bg-gradient-to-r data-[state=active]:from-[rgba(14,36,64,0.8)] data-[state=active]:to-[rgba(14,36,64,0.6)]',
                            'data-[state=active]:text-cyan-400',
                            'data-[state=active]:shadow-lg',
                            'data-[state=active]:border data-[state=active]:border-[rgba(56,189,248,0.2)]',
                            // Focus
                            'focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50'
                        )}
                    >
                        {tab.icon}
                        {tab.label}
                    </Tabs.Trigger>
                ))}
            </Tabs.List>
            {children}
        </Tabs.Root>
    );
};

const GlassTabContent: React.FC<GlassTabContentProps> = ({
    value,
    children,
    className,
}) => {
    return (
        <Tabs.Content
            value={value}
            className={cn(
                'animate-fade-in',
                'focus:outline-none',
                className
            )}
        >
            {children}
        </Tabs.Content>
    );
};

export { GlassTabs, GlassTabContent };
export default GlassTabs;
