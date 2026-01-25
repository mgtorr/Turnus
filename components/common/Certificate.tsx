import React from 'react';
import { cn } from '../../lib/utils';
import Logo from './Logo';

interface CertificateProps {
    userName: string;
    courseName: string;
    language: string;
    date: string;
    className?: string;
}

const Certificate: React.FC<CertificateProps> = ({ userName, courseName, language, date, className }) => {
    return (
        <div className={cn(
            'relative p-10 max-w-2xl mx-auto text-center',
            // Glass effect with warm gold accents
            'bg-gradient-to-br from-[rgba(14,36,64,0.95)] to-[rgba(14,36,64,0.85)]',
            'backdrop-blur-2xl',
            'rounded-3xl',
            // Gold double border effect
            'border-4 border-amber-500/30',
            'ring-2 ring-amber-500/20 ring-offset-4 ring-offset-[#030712]',
            // Shadow
            'shadow-2xl shadow-black/50',
            className
        )}>
            {/* Corner decorations */}
            <div className="absolute top-4 left-4 w-8 h-8 border-l-2 border-t-2 border-amber-500/50 rounded-tl-lg" />
            <div className="absolute top-4 right-4 w-8 h-8 border-r-2 border-t-2 border-amber-500/50 rounded-tr-lg" />
            <div className="absolute bottom-4 left-4 w-8 h-8 border-l-2 border-b-2 border-amber-500/50 rounded-bl-lg" />
            <div className="absolute bottom-4 right-4 w-8 h-8 border-r-2 border-b-2 border-amber-500/50 rounded-br-lg" />

            {/* Watermark */}
            <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] pointer-events-none">
                <Logo className="w-64 h-64" />
            </div>

            {/* Decorative glow */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/2 h-32 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="relative z-10">
                <div className="flex justify-center mb-6">
                    <Logo className="w-16 h-16" />
                </div>

                <h1 className="text-4xl md:text-5xl font-black mb-2 uppercase tracking-widest bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
                    Certificate
                </h1>
                <h2 className="text-lg text-amber-500/70 uppercase tracking-wide mb-8 font-semibold">of Completion</h2>

                <p className="text-lg text-[#94a3b8] italic mb-4">This certifies that</p>

                <div className="relative inline-block min-w-[300px] mb-6">
                    <div className="text-3xl md:text-4xl font-bold text-[#f0f9ff] pb-2">
                        {userName}
                    </div>
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-amber-500/50 to-transparent" />
                </div>

                <p className="text-lg text-[#94a3b8] italic mb-2">has successfully mastered the lesson</p>

                <h3 className="text-2xl font-bold text-gradient mb-1">{courseName}</h3>
                <p className="text-md text-[#64748b] mb-8">in {language}</p>

                <div className="flex justify-between items-end mt-12 px-4">
                    <div className="text-left">
                        <div className="w-28 h-0.5 bg-gradient-to-r from-amber-500/50 to-transparent mb-2" />
                        <p className="text-xs text-[#64748b]">Date: {date}</p>
                    </div>

                    <div className="flex flex-col items-center">
                        <div className={cn(
                            'w-20 h-20 rounded-full flex items-center justify-center flex-col',
                            'border-2 border-amber-500/50',
                            'bg-gradient-to-br from-amber-500/10 to-orange-500/10',
                            'text-amber-400 font-bold text-[10px] leading-tight',
                            'transform rotate-12',
                            'shadow-lg shadow-amber-500/20'
                        )}>
                            <span>VERIFIED</span>
                            <span className="text-[8px] text-amber-500/70 mt-0.5">AI TUTOR</span>
                        </div>
                    </div>

                    <div className="text-right">
                        <div className="w-28 h-0.5 bg-gradient-to-l from-amber-500/50 to-transparent mb-2 ml-auto" />
                        <p className="text-xs text-[#64748b]">FluentFlow AI</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Certificate;
