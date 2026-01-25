import React from 'react';
import { cn } from '../../lib/utils';

interface BackgroundProps {
    className?: string;
}

const Background: React.FC<BackgroundProps> = ({ className }) => {
    return (
        <div className={cn('fixed inset-0 -z-10 overflow-hidden', className)}>
            {/* Base gradient */}
            <div className="absolute inset-0 bg-[#030712]" />

            {/* Mesh gradient overlay */}
            <div
                className="absolute inset-0"
                style={{
                    background: `
                        radial-gradient(ellipse 80% 50% at 0% 0%, rgba(6, 182, 212, 0.15) 0%, transparent 50%),
                        radial-gradient(ellipse 60% 40% at 100% 0%, rgba(20, 184, 166, 0.12) 0%, transparent 50%),
                        radial-gradient(ellipse 50% 50% at 100% 100%, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
                        radial-gradient(ellipse 70% 60% at 0% 100%, rgba(6, 182, 212, 0.08) 0%, transparent 50%)
                    `,
                }}
            />

            {/* Floating orbs */}
            <div
                className="absolute top-[10%] left-[5%] w-[40vw] h-[40vw] max-w-[600px] max-h-[600px] rounded-full floating-orb"
                style={{
                    background: 'radial-gradient(circle, rgba(6, 182, 212, 0.15) 0%, transparent 70%)',
                    filter: 'blur(60px)',
                }}
            />
            <div
                className="absolute top-[60%] right-[10%] w-[30vw] h-[30vw] max-w-[500px] max-h-[500px] rounded-full floating-orb-delayed"
                style={{
                    background: 'radial-gradient(circle, rgba(20, 184, 166, 0.12) 0%, transparent 70%)',
                    filter: 'blur(80px)',
                }}
            />
            <div
                className="absolute bottom-[5%] left-[30%] w-[25vw] h-[25vw] max-w-[400px] max-h-[400px] rounded-full floating-orb"
                style={{
                    background: 'radial-gradient(circle, rgba(139, 92, 246, 0.1) 0%, transparent 70%)',
                    filter: 'blur(70px)',
                    animationDelay: '-10s',
                }}
            />

            {/* Noise texture overlay */}
            <div
                className="absolute inset-0 pointer-events-none"
                style={{
                    backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
                    opacity: 0.03,
                }}
            />

            {/* Vignette effect */}
            <div
                className="absolute inset-0 pointer-events-none"
                style={{
                    background: 'radial-gradient(ellipse at center, transparent 0%, rgba(3, 7, 18, 0.4) 100%)',
                }}
            />
        </div>
    );
};

export default Background;
