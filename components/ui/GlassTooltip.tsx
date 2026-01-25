import React from 'react';
import * as Tooltip from '@radix-ui/react-tooltip';
import { cn } from '../../lib/utils';

interface GlassTooltipProps {
    children: React.ReactNode;
    content: React.ReactNode;
    side?: 'top' | 'right' | 'bottom' | 'left';
    align?: 'start' | 'center' | 'end';
    delayDuration?: number;
}

const GlassTooltip: React.FC<GlassTooltipProps> = ({
    children,
    content,
    side = 'top',
    align = 'center',
    delayDuration = 200,
}) => {
    return (
        <Tooltip.Provider delayDuration={delayDuration}>
            <Tooltip.Root>
                <Tooltip.Trigger asChild>
                    {children}
                </Tooltip.Trigger>
                <Tooltip.Portal>
                    <Tooltip.Content
                        side={side}
                        align={align}
                        sideOffset={8}
                        className={cn(
                            'z-50 px-4 py-2.5 rounded-xl',
                            'bg-gradient-to-br from-[rgba(14,36,64,0.95)] to-[rgba(14,36,64,0.85)]',
                            'backdrop-blur-xl',
                            'border border-[rgba(56,189,248,0.2)]',
                            'shadow-xl shadow-black/30',
                            'text-sm text-[#f0f9ff]',
                            // Animation
                            'data-[state=delayed-open]:animate-fade-in',
                            'data-[state=closed]:animate-fade-out'
                        )}
                    >
                        {content}
                        <Tooltip.Arrow
                            className="fill-[rgba(14,36,64,0.95)]"
                            width={12}
                            height={6}
                        />
                    </Tooltip.Content>
                </Tooltip.Portal>
            </Tooltip.Root>
        </Tooltip.Provider>
    );
};

export default GlassTooltip;
