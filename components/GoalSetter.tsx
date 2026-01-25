import React, { useState } from 'react';
import type { UserProfile } from '../types';
import { LanguageLevel, LearningGoal } from '../types';
import { LANGUAGE_LEVELS, LEARNING_GOALS, LANGUAGES } from '../constants';
import GlassCard from './ui/GlassCard';
import GlassButton from './ui/GlassButton';
import GlassInput from './ui/GlassInput';
import Background from './layout/Background';
import { cn } from '../lib/utils';

interface GoalSetterProps {
    onProfileCreate: (profile: UserProfile) => void;
    showWarning?: (message: string) => void;
}

// Logo component
const Logo: React.FC<{ className?: string }> = ({ className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" className={className} fill="none">
        <defs>
            <linearGradient id="logoGradientGoal" x1="10" y1="10" x2="90" y2="90" gradientUnits="userSpaceOnUse">
                <stop stopColor="#06b6d4" />
                <stop offset="1" stopColor="#14b8a6" />
            </linearGradient>
        </defs>
        <path
            d="M20 50C20 33.4315 33.4315 20 50 20C66.5685 20 80 33.4315 80 50C80 60 75 69 67 74L65 85L55 80C53.3 80.2 51.7 80.2 50 80.2C33.4 80.2 20 66.8 20 50Z"
            fill="url(#logoGradientGoal)"
            fillOpacity="0.15"
        />
        <path
            d="M35 50C35 50 42 42 50 42C58 42 65 50 65 50"
            stroke="url(#logoGradientGoal)"
            strokeWidth="6"
            strokeLinecap="round"
            strokeLinejoin="round"
        />
        <path
            d="M35 50C35 50 42 58 50 58C58 58 65 50 65 50"
            stroke="url(#logoGradientGoal)"
            strokeWidth="6"
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity="0.7"
        />
        <circle cx="72" cy="28" r="4" fill="#06b6d4" />
    </svg>
);

const GoalSetter: React.FC<GoalSetterProps> = ({ onProfileCreate, showWarning }) => {
    const [name, setName] = useState('');
    const [language, setLanguage] = useState(LANGUAGES[0]);
    const [level, setLevel] = useState(LANGUAGE_LEVELS[0]);
    const [goals, setGoals] = useState<LearningGoal[]>([]);

    const handleGoalToggle = (goal: LearningGoal) => {
        setGoals(prev =>
            prev.includes(goal) ? prev.filter(g => g !== goal) : [...prev, goal]
        );
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (name && language && level && goals.length > 0) {
            onProfileCreate({ name, language, level, goals });
        } else {
            if (showWarning) {
                showWarning('Please fill out all fields and select at least one goal.');
            } else {
                alert('Please fill out all fields and select at least one goal.');
            }
        }
    };

    return (
        <div className="min-h-screen relative flex items-center justify-center p-4 overflow-hidden">
            <Background />

            <div className="w-full max-w-2xl relative z-10">
                {/* Logo & Title */}
                <div className="text-center mb-10">
                    <div className="inline-block p-5 rounded-3xl bg-[rgba(14,36,64,0.5)] backdrop-blur-2xl border border-[rgba(56,189,248,0.2)] shadow-2xl mb-6">
                        <Logo className="w-20 h-20" />
                    </div>
                    <h1 className="text-5xl font-black text-[#f0f9ff] tracking-tight">
                        Fluent<span className="text-gradient">Flow</span>
                    </h1>
                    <p className="text-lg text-[#94a3b8] mt-3">
                        Design your personalized path to fluency.
                    </p>
                </div>

                {/* Form Card */}
                <GlassCard className="!bg-[rgba(14,36,64,0.5)]">
                    <form onSubmit={handleSubmit} className="space-y-8">
                        {/* Name Input */}
                        <GlassInput
                            label="Your Name"
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="e.g. Alex"
                            required
                        />

                        {/* Language & Level */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-bold text-cyan-100 uppercase tracking-wider mb-2 ml-1">
                                    Target Language
                                </label>
                                <div className="relative">
                                    <select
                                        value={language}
                                        onChange={(e) => setLanguage(e.target.value)}
                                        className={cn(
                                            'w-full appearance-none cursor-pointer',
                                            'bg-[rgba(14,36,64,0.6)]',
                                            'backdrop-blur-xl',
                                            'border border-[rgba(56,189,248,0.15)]',
                                            'rounded-xl',
                                            'text-[#f0f9ff]',
                                            'px-4 py-4',
                                            'focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20',
                                            'transition-all duration-200'
                                        )}
                                    >
                                        {LANGUAGES.map((lang) => (
                                            <option key={lang} value={lang} className="bg-[#0a1628]">
                                                {lang}
                                            </option>
                                        ))}
                                    </select>
                                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-[#64748b]">
                                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-bold text-cyan-100 uppercase tracking-wider mb-2 ml-1">
                                    Current Level
                                </label>
                                <div className="relative">
                                    <select
                                        value={level}
                                        onChange={(e) => setLevel(e.target.value as LanguageLevel)}
                                        className={cn(
                                            'w-full appearance-none cursor-pointer',
                                            'bg-[rgba(14,36,64,0.6)]',
                                            'backdrop-blur-xl',
                                            'border border-[rgba(56,189,248,0.15)]',
                                            'rounded-xl',
                                            'text-[#f0f9ff]',
                                            'px-4 py-4',
                                            'focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20',
                                            'transition-all duration-200'
                                        )}
                                    >
                                        {LANGUAGE_LEVELS.map((lvl) => (
                                            <option key={lvl} value={lvl} className="bg-[#0a1628]">
                                                {lvl}
                                            </option>
                                        ))}
                                    </select>
                                    <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-[#64748b]">
                                        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Learning Goals */}
                        <div>
                            <label className="block text-sm font-bold text-cyan-100 uppercase tracking-wider mb-3 ml-1">
                                Why are you learning?
                            </label>
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                                {LEARNING_GOALS.map((goal) => (
                                    <button
                                        type="button"
                                        key={goal}
                                        onClick={() => handleGoalToggle(goal)}
                                        className={cn(
                                            'px-4 py-3.5 text-sm font-medium rounded-xl',
                                            'border transition-all duration-200',
                                            goals.includes(goal)
                                                ? [
                                                    'bg-gradient-to-r from-cyan-500 to-teal-500',
                                                    'border-transparent',
                                                    'text-white',
                                                    'shadow-lg shadow-cyan-500/30',
                                                    'scale-105',
                                                ]
                                                : [
                                                    'bg-[rgba(14,36,64,0.4)]',
                                                    'border-[rgba(56,189,248,0.15)]',
                                                    'text-[#94a3b8]',
                                                    'hover:bg-[rgba(14,36,64,0.6)]',
                                                    'hover:border-[rgba(56,189,248,0.3)]',
                                                    'hover:text-[#f0f9ff]',
                                                ]
                                        )}
                                    >
                                        {goal}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Submit Button */}
                        <GlassButton
                            type="submit"
                            variant="primary"
                            size="lg"
                            className="w-full"
                        >
                            Generate Learning Plan
                        </GlassButton>
                    </form>
                </GlassCard>
            </div>
        </div>
    );
};

export default GoalSetter;
