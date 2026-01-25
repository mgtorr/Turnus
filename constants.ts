
import { LanguageLevel, LearningGoal, SkillType, Achievement } from './types';

export const LANGUAGE_LEVELS: LanguageLevel[] = Object.values(LanguageLevel);
export const LEARNING_GOALS: LearningGoal[] = Object.values(LearningGoal);
export const LANGUAGES: string[] = ["Spanish", "French", "German", "Italian", "Japanese", "Mandarin", "English", "Norwegian", "Swedish", "Danish"];

export const SKILL_COLORS: Record<SkillType, string> = {
    [SkillType.WRITING]: 'bg-sky-500 border-sky-500 text-sky-600',
    [SkillType.ORAL]: 'bg-emerald-500 border-emerald-500 text-emerald-600',
    [SkillType.TEST]: 'bg-amber-500 border-amber-500 text-amber-600',
    [SkillType.GENERAL]: 'bg-indigo-500 border-indigo-500 text-indigo-600',
};

export const MOCK_ACHIEVEMENTS: Achievement[] = [
    { id: '1', title: 'First Steps', description: 'Complete your first lesson', icon: '🌱', unlocked: true },
    { id: '2', title: 'Week Warrior', description: 'Maintain a 7-day streak', icon: '🔥', unlocked: true },
    { id: '3', title: 'Wordsmith', description: 'Write over 1000 words total', icon: '✍️', unlocked: false },
    { id: '4', title: 'Polyglot', description: 'Learn phrases in 3 languages', icon: '🌍', unlocked: false },
    { id: '5', title: 'Perfect Score', description: 'Get 100% on a final assignment', icon: '🏆', unlocked: true },
    { id: '6', title: 'Night Owl', description: 'Complete a lesson after 10 PM', icon: '🦉', unlocked: false },
];
