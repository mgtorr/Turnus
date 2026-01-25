import React from 'react';
import type { UserProfile, UserStats } from '../types';
import { SkillType } from '../types';
import GlassCard from './ui/GlassCard';

import Avatar from './ui/Avatar';
import { cn } from '../lib/utils';

interface ProfilePageProps {
    userProfile: UserProfile;
    stats: UserStats;
}

// Skill color mapping
const SKILL_VARIANTS: Record<SkillType, 'cyan' | 'teal' | 'gold' | 'violet'> = {
    [SkillType.WRITING]: 'cyan',
    [SkillType.ORAL]: 'teal',
    [SkillType.TEST]: 'gold',
    [SkillType.GENERAL]: 'violet',
};

const ProfilePage: React.FC<ProfilePageProps> = ({ userProfile, stats }) => {
    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header */}
            <header>
                <h1 className="text-4xl font-black text-[#f0f9ff] tracking-tight">
                    Your <span className="text-gradient">Profile</span>
                </h1>
                <p className="text-[#94a3b8] mt-2">
                    Track your progress and achievements.
                </p>
            </header>

            {/* Profile Header Card */}
            <GlassCard padding="none" className="overflow-hidden" hover={false}>
                {/* Banner */}
                <div className="h-32 bg-gradient-to-r from-cyan-500/30 via-teal-500/30 to-violet-500/30 relative">
                    <div className="absolute inset-0 bg-[url('data:image/svg+xml,...')] opacity-5" />
                </div>

                {/* Profile Info */}
                <div className="px-8 pb-8">
                    <div className="relative flex items-end -mt-12 mb-6">
                        <Avatar
                            fallback={userProfile.name}
                            size="xl"
                            ring
                            ringColor="cyan"
                        />
                        <div className="ml-6 mb-2">
                            <h2 className="text-3xl font-bold text-[#f0f9ff]">
                                {userProfile.name}
                            </h2>
                            <p className="text-[#94a3b8]">
                                Learning <span className="text-cyan-400">{userProfile.language}</span>
                                <span className="mx-2">•</span>
                                {userProfile.level}
                            </p>
                        </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 border-t border-[rgba(56,189,248,0.1)]">
                        <div className="text-center p-4 rounded-xl bg-[rgba(14,36,64,0.3)]">
                            <span className="block text-3xl font-black text-gradient">
                                {stats.streakDays}
                            </span>
                            <span className="text-xs font-medium text-[#64748b] uppercase tracking-wide">
                                Day Streak
                            </span>
                        </div>
                        <div className="text-center p-4 rounded-xl bg-[rgba(14,36,64,0.3)]">
                            <span className="block text-3xl font-black text-amber-400">
                                {stats.totalXp}
                            </span>
                            <span className="text-xs font-medium text-[#64748b] uppercase tracking-wide">
                                Total XP
                            </span>
                        </div>
                        <div className="text-center p-4 rounded-xl bg-[rgba(14,36,64,0.3)]">
                            <span className="block text-3xl font-black text-teal-400">
                                {stats.lessonsCompleted}
                            </span>
                            <span className="text-xs font-medium text-[#64748b] uppercase tracking-wide">
                                Lessons Done
                            </span>
                        </div>
                        <div className="text-center p-4 rounded-xl bg-[rgba(14,36,64,0.3)]">
                            <span className="block text-3xl font-black text-violet-400">
                                {stats.wordsWritten}
                            </span>
                            <span className="text-xs font-medium text-[#64748b] uppercase tracking-wide">
                                Words Written
                            </span>
                        </div>
                    </div>
                </div>
            </GlassCard>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Skills Section */}
                <div className="lg:col-span-2 space-y-8">
                    <GlassCard title="Skill Proficiency">
                        <div className="space-y-6">
                            {(Object.keys(stats.skillLevels) as SkillType[]).map((skill) => {
                                const percentage = stats.skillLevels[skill];
                                const variant = SKILL_VARIANTS[skill];

                                return (
                                    <GlassProgress
                                        key={skill}
                                        value={percentage}
                                        variant={variant}
                                        size="md"
                                        label={skill}
                                        showLabel
                                    />
                                );
                            })}
                        </div>
                    </GlassCard>

                    {/* Certifications */}
                    <GlassCard title="Certifications">
                        {stats.certificates.length > 0 ? (
                            <div className="space-y-4">
                                {stats.certificates.map(cert => (
                                    <div
                                        key={cert.id}
                                        className={cn(
                                            'flex items-center justify-between p-4 rounded-xl',
                                            'bg-[rgba(14,36,64,0.4)]',
                                            'border border-[rgba(56,189,248,0.1)]',
                                            'hover:bg-[rgba(14,36,64,0.6)]',
                                            'transition-all duration-200'
                                        )}
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="w-12 h-12 rounded-full bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 flex items-center justify-center">
                                                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                                                </svg>
                                            </div>
                                            <div>
                                                <h4 className="font-bold text-[#f0f9ff]">{cert.courseName}</h4>
                                                <p className="text-xs text-[#64748b]">Completed on {cert.date}</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <span className="block text-lg font-bold text-emerald-400">{cert.score}%</span>
                                            <span className="text-xs text-[#64748b]">Score</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[rgba(14,36,64,0.4)] flex items-center justify-center">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-[#64748b]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                                    </svg>
                                </div>
                                <p className="text-[#94a3b8]">
                                    No certificates earned yet. Complete a lesson with high marks!
                                </p>
                            </div>
                        )}
                    </GlassCard>
                </div>

                {/* Achievements */}
                <div>
                    <GlassCard title="Achievements">
                        <div className="grid grid-cols-3 gap-4">
                            {stats.achievements.map(badge => (
                                <div
                                    key={badge.id}
                                    className="flex flex-col items-center text-center group"
                                >
                                    <div
                                        className={cn(
                                            'w-16 h-16 rounded-full flex items-center justify-center text-2xl mb-2',
                                            'border-2 transition-all transform group-hover:scale-110',
                                            badge.unlocked
                                                ? [
                                                    'bg-gradient-to-br from-amber-500/20 to-orange-500/20',
                                                    'border-amber-500/50',
                                                    'shadow-lg shadow-amber-500/20',
                                                ]
                                                : [
                                                    'bg-[rgba(14,36,64,0.4)]',
                                                    'border-[rgba(56,189,248,0.1)]',
                                                    'grayscale opacity-50',
                                                ]
                                        )}
                                    >
                                        {badge.icon}
                                    </div>
                                    <span
                                        className={cn(
                                            'text-xs font-bold',
                                            badge.unlocked ? 'text-[#f0f9ff]' : 'text-[#64748b]'
                                        )}
                                    >
                                        {badge.title}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </GlassCard>
                </div>
            </div>
        </div>
    );
};

export default ProfilePage;
