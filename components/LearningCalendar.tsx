import React, { useState } from 'react';
import type { CalendarEvent, LearningTask } from '../types';
import { SkillType } from '../types';
import GlassCard from './ui/GlassCard';
import GlassButton from './ui/GlassButton';
import GlassTooltip from './ui/GlassTooltip';
import { cn } from '../lib/utils';

interface LearningCalendarProps {
    events: CalendarEvent[];
    addEvent: (event: CalendarEvent) => void;
    onTaskClick: (task: LearningTask) => void;
}

// Skill colors for ocean theme
const SKILL_COLORS: Record<SkillType, string> = {
    [SkillType.WRITING]: 'bg-gradient-to-r from-cyan-500 to-blue-500',
    [SkillType.ORAL]: 'bg-gradient-to-r from-emerald-500 to-teal-500',
    [SkillType.TEST]: 'bg-gradient-to-r from-amber-500 to-orange-500',
    [SkillType.GENERAL]: 'bg-gradient-to-r from-violet-500 to-purple-500',
};

const LearningCalendar: React.FC<LearningCalendarProps> = ({ events, onTaskClick }) => {
    const [currentDate, setCurrentDate] = useState(new Date());

    const startOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
    const endOfMonth = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
    const startDay = startOfMonth.getDay();
    const daysInMonth = endOfMonth.getDate();

    const days = (Array.from({ length: startDay }, (_, _i) => null) as (number | null)[]).concat(
        Array.from({ length: daysInMonth }, (_, _i) => _i + 1)
    );

    const getEventsForDate = (date: number | null) => {
        if (!date) return [];
        const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(date).padStart(2, '0')}`;
        return events.filter(event => event.date === dateStr);
    };

    const changeMonth = (offset: number) => {
        setCurrentDate(prev => new Date(prev.getFullYear(), prev.getMonth() + offset, 1));
    };

    const handleEventClick = (event: CalendarEvent) => {
        const task: LearningTask = {
            skill: event.skill,
            topic: event.title,
            description: event.description || '',
            durationMinutes: event.durationMinutes || 15
        };
        onTaskClick(task);
    };

    const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const today = new Date();
    const isToday = (day: number | null) => {
        if (!day) return false;
        return (
            today.getDate() === day &&
            today.getMonth() === currentDate.getMonth() &&
            today.getFullYear() === currentDate.getFullYear()
        );
    };

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <header>
                <h1 className="text-4xl font-black text-[#f0f9ff] tracking-tight">
                    Learning <span className="text-gradient">Calendar</span>
                </h1>
                <p className="text-[#94a3b8] mt-2">
                    Track your learning schedule and stay consistent.
                </p>
            </header>

            <GlassCard padding="lg">
                {/* Month Navigation */}
                <div className="flex justify-between items-center mb-6">
                    <GlassButton
                        variant="ghost"
                        size="sm"
                        onClick={() => changeMonth(-1)}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                    </GlassButton>

                    <h2 className="text-2xl font-bold text-[#f0f9ff]">
                        {currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}
                    </h2>

                    <GlassButton
                        variant="ghost"
                        size="sm"
                        onClick={() => changeMonth(1)}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                    </GlassButton>
                </div>

                {/* Calendar Grid */}
                <div className="grid grid-cols-7 gap-1">
                    {/* Weekday Headers */}
                    {weekdays.map(day => (
                        <div
                            key={day}
                            className="text-center font-bold text-sm text-[#64748b] py-3 uppercase tracking-wider"
                        >
                            {day}
                        </div>
                    ))}

                    {/* Days */}
                    {days.map((day, index) => {
                        const dayEvents = getEventsForDate(day);
                        const todayClass = isToday(day);

                        return (
                            <div
                                key={index}
                                className={cn(
                                    'min-h-[120px] p-2 rounded-xl border transition-all duration-200',
                                    day
                                        ? [
                                            'bg-[rgba(14,36,64,0.3)]',
                                            'border-[rgba(56,189,248,0.1)]',
                                            'hover:bg-[rgba(14,36,64,0.5)]',
                                            'hover:border-[rgba(56,189,248,0.2)]',
                                        ]
                                        : 'bg-transparent border-transparent'
                                )}
                            >
                                {day && (
                                    <>
                                        <span
                                            className={cn(
                                                'inline-flex items-center justify-center w-7 h-7 rounded-full text-sm font-semibold mb-2',
                                                todayClass
                                                    ? 'bg-gradient-to-r from-cyan-500 to-teal-500 text-white'
                                                    : 'text-[#94a3b8]'
                                            )}
                                        >
                                            {day}
                                        </span>

                                        <div className="space-y-1 overflow-y-auto max-h-[80px] custom-scrollbar">
                                            {dayEvents.map(event => (
                                                <GlassTooltip
                                                    key={event.id}
                                                    content={
                                                        <div className="max-w-xs">
                                                            <p className="font-bold mb-1">{event.title}</p>
                                                            {event.description && (
                                                                <p className="text-sm text-[#94a3b8]">{event.description}</p>
                                                            )}
                                                            {event.durationMinutes && (
                                                                <p className="text-xs text-cyan-400 mt-1">
                                                                    {event.durationMinutes} minutes
                                                                </p>
                                                            )}
                                                        </div>
                                                    }
                                                    side="top"
                                                >
                                                    <button
                                                        onClick={() => handleEventClick(event)}
                                                        className={cn(
                                                            'w-full text-left p-2 rounded-lg text-xs text-white truncate',
                                                            'transition-all duration-200',
                                                            'hover:opacity-90 hover:shadow-md',
                                                            'transform hover:scale-[1.02]',
                                                            SKILL_COLORS[event.skill]
                                                        )}
                                                    >
                                                        {event.title}
                                                    </button>
                                                </GlassTooltip>
                                            ))}
                                        </div>
                                    </>
                                )}
                            </div>
                        );
                    })}
                </div>

                {/* Legend */}
                <div className="mt-6 pt-6 border-t border-[rgba(56,189,248,0.1)]">
                    <div className="flex flex-wrap items-center gap-4 text-sm">
                        <span className="text-[#64748b] font-medium">Skills:</span>
                        {Object.entries(SkillType).map(([key, value]) => (
                            <div key={key} className="flex items-center gap-2">
                                <div className={cn('w-3 h-3 rounded', SKILL_COLORS[value])} />
                                <span className="text-[#94a3b8]">{value}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Tip */}
                <div className="mt-4 flex items-center gap-2 text-xs text-[#64748b]">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-cyan-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                    <span>Click on any event to start the lesson directly.</span>
                </div>
            </GlassCard>
        </div>
    );
};

export default LearningCalendar;
