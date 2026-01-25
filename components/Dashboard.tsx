import React from 'react';
import type { UserProfile, LearningPlan, LearningTask, DailyChallenge } from '../types';
import { SkillType } from '../types';
import GlassCard from './ui/GlassCard';
import GlassButton from './ui/GlassButton';
import Badge from './ui/Badge';
import { cn } from '../lib/utils';

interface DashboardProps {
    userProfile: UserProfile;
    learningPlan: LearningPlan;
    dailyChallenge: DailyChallenge | null;
    onPlanUpdate: (plan: LearningPlan) => void;
    onTaskClick: (task: LearningTask) => void;
}

// Skill color mapping for ocean theme
const SKILL_STYLES: Record<SkillType, { bg: string; text: string; glow: string }> = {
    [SkillType.WRITING]: {
        bg: 'from-cyan-500 to-blue-500',
        text: 'text-cyan-400',
        glow: 'shadow-cyan-500/30',
    },
    [SkillType.ORAL]: {
        bg: 'from-emerald-500 to-teal-500',
        text: 'text-emerald-400',
        glow: 'shadow-emerald-500/30',
    },
    [SkillType.TEST]: {
        bg: 'from-amber-500 to-orange-500',
        text: 'text-amber-400',
        glow: 'shadow-amber-500/30',
    },
    [SkillType.GENERAL]: {
        bg: 'from-violet-500 to-purple-500',
        text: 'text-violet-400',
        glow: 'shadow-violet-500/30',
    },
};

const Dashboard: React.FC<DashboardProps> = ({
    userProfile,
    learningPlan,
    dailyChallenge,
    onTaskClick,
}) => {
    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header */}
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-4xl md:text-5xl font-black text-[#f0f9ff] tracking-tight">
                        Hello, <span className="text-gradient">{userProfile.name}</span>
                    </h1>
                    <p className="text-[#94a3b8] mt-2 text-lg">
                        Let's continue your flow today.
                    </p>
                </div>
                <div className="px-5 py-2.5 rounded-2xl bg-[rgba(14,36,64,0.6)] backdrop-blur-xl border border-[rgba(56,189,248,0.15)] text-sm font-medium text-[#94a3b8]">
                    {new Date().toLocaleDateString(undefined, {
                        weekday: 'long',
                        month: 'long',
                        day: 'numeric',
                    })}
                </div>
            </header>

            {/* Bento Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Current Status Card */}
                <GlassCard title="Current Status" className="md:row-span-1">
                    <div className="space-y-4">
                        <div className="flex justify-between items-center p-4 rounded-xl bg-[rgba(14,36,64,0.4)] border border-[rgba(56,189,248,0.1)]">
                            <span className="text-[#64748b] text-sm font-semibold">
                                Target Language
                            </span>
                            <span className="font-bold text-cyan-400">
                                {userProfile.language}
                            </span>
                        </div>
                        <div className="flex justify-between items-center p-4 rounded-xl bg-[rgba(14,36,64,0.4)] border border-[rgba(56,189,248,0.1)]">
                            <span className="text-[#64748b] text-sm font-semibold">
                                Proficiency
                            </span>
                            <span className="font-bold text-teal-400">
                                {userProfile.level}
                            </span>
                        </div>
                        <div className="p-4 rounded-xl bg-[rgba(14,36,64,0.4)] border border-[rgba(56,189,248,0.1)]">
                            <span className="text-[#64748b] text-sm font-semibold block mb-3">
                                Focus Goals
                            </span>
                            <div className="flex flex-wrap gap-2">
                                {userProfile.goals.map((g) => (
                                    <Badge key={g} variant="info" size="sm">
                                        {g}
                                    </Badge>
                                ))}
                            </div>
                        </div>
                    </div>
                </GlassCard>

                {/* Weekly Focus Card */}
                <GlassCard className="md:col-span-2 relative overflow-hidden group" hover={false}>
                    <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/5 to-teal-500/5 opacity-50 group-hover:opacity-100 transition-opacity duration-500" />
                    <div className="absolute top-4 right-4 text-6xl opacity-10">
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-20 h-20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                        </svg>
                    </div>
                    <div className="relative z-10">
                        <h2 className="text-sm font-bold text-cyan-400 uppercase tracking-wider mb-4">
                            Weekly Focus
                        </h2>
                        <p className="text-2xl md:text-3xl font-medium text-[#f0f9ff] leading-relaxed">
                            "{learningPlan.weeklyFocus}"
                        </p>
                        <div className="mt-6 flex items-center gap-2 text-sm font-bold text-cyan-400 uppercase tracking-wider">
                            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                            <span>Active Goal</span>
                        </div>
                    </div>
                </GlassCard>

                {/* Daily Challenge Card */}
                {dailyChallenge && (
                    <GlassCard
                        className="md:col-span-3 !p-0 overflow-hidden"
                        padding="none"
                        hover={false}
                    >
                        <div className="relative bg-gradient-to-r from-amber-500/20 via-orange-500/20 to-rose-500/20 p-8">
                            {/* Gold border effect */}
                            <div className="absolute inset-0 border-2 border-amber-500/20 rounded-3xl" />

                            {/* Background decoration */}
                            <div className="absolute top-0 right-0 p-4 opacity-10">
                                <svg className="w-32 h-32" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm0 14c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm5-7h-2v2h-2v-2h-2v-2h2V6h2v2h2v2z" />
                                </svg>
                            </div>

                            <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                                <div>
                                    <Badge variant="gold" className="mb-3">
                                        Daily Challenge
                                    </Badge>
                                    <h3 className="text-2xl md:text-3xl font-black text-[#f0f9ff] mb-2">
                                        {dailyChallenge.title}
                                    </h3>
                                    <p className="text-[#94a3b8] max-w-xl">
                                        {dailyChallenge.description}
                                    </p>
                                    <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[rgba(14,36,64,0.5)] border border-amber-500/20">
                                        <span className="text-amber-400 font-bold">
                                            +{dailyChallenge.rewardXp} XP
                                        </span>
                                        <span className="text-[#64748b]">Reward</span>
                                    </div>
                                </div>
                                <GlassButton
                                    variant="gold"
                                    size="lg"
                                    onClick={() => onTaskClick(dailyChallenge.task)}
                                    icon={
                                        <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                                        </svg>
                                    }
                                    iconPosition="right"
                                >
                                    Start Challenge
                                </GlassButton>
                            </div>
                        </div>
                    </GlassCard>
                )}
            </div>

            {/* Tasks Section */}
            <GlassCard title="Your Tasks" subtitle="Click on a task to begin your lesson">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {learningPlan.tasks.map((task, index) => {
                        const skillStyle = SKILL_STYLES[task.skill];

                        return (
                            <button
                                key={index}
                                onClick={() => onTaskClick(task)}
                                className={cn(
                                    'group relative flex items-start gap-4 p-5',
                                    'rounded-2xl text-left',
                                    'bg-[rgba(14,36,64,0.4)]',
                                    'border border-[rgba(56,189,248,0.1)]',
                                    'transition-all duration-300',
                                    'hover:bg-[rgba(14,36,64,0.6)]',
                                    'hover:border-[rgba(6,182,212,0.3)]',
                                    'hover:shadow-lg hover:shadow-cyan-500/10',
                                    'hover:-translate-y-1'
                                )}
                            >
                                {/* Skill Icon */}
                                <div
                                    className={cn(
                                        'w-14 h-14 rounded-2xl flex items-center justify-center',
                                        'text-white font-bold text-lg',
                                        'bg-gradient-to-br',
                                        skillStyle.bg,
                                        'shadow-lg',
                                        skillStyle.glow,
                                        'transform group-hover:scale-110 transition-transform duration-300',
                                        'shrink-0'
                                    )}
                                >
                                    {task.skill.substring(0, 1)}
                                </div>

                                {/* Content */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex justify-between items-start mb-2">
                                        <h3 className={cn(
                                            'font-bold text-[#f0f9ff] truncate pr-2',
                                            'group-hover:text-cyan-400 transition-colors'
                                        )}>
                                            {task.topic}
                                        </h3>
                                        <span className="text-xs font-bold text-[#64748b] bg-[rgba(14,36,64,0.5)] px-2.5 py-1 rounded-lg border border-[rgba(56,189,248,0.1)] shrink-0">
                                            {task.durationMinutes} min
                                        </span>
                                    </div>
                                    <p className="text-sm text-[#94a3b8] line-clamp-2">
                                        {task.description}
                                    </p>
                                </div>

                                {/* Arrow */}
                                <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-x-2 group-hover:translate-x-0">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                    </svg>
                                </div>
                            </button>
                        );
                    })}
                </div>
            </GlassCard>
        </div>
    );
};

export default Dashboard;
