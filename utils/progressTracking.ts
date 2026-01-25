import type { UserStats, LearningTask, AssignmentEvaluation } from '../types';
import { SkillType } from '../types';

// XP reward constants
export const XP_REWARDS = {
    QUIZ_CORRECT: 20,
    QUIZ_PERFECT_SECTION: 50,
    ASSIGNMENT_BASE: 100,
    ASSIGNMENT_BONUS_PER_10_POINTS: 10, // Bonus XP for every 10 points above 70
    DAILY_CHALLENGE: 75,
    VOCABULARY_WORD: 15,
    STREAK_BONUS: 25,
} as const;

// Skill type mapping for XP distribution
export const SKILL_XP_WEIGHTS = {
    [SkillType.WRITING]: 1.2,
    [SkillType.ORAL]: 1.3,
    [SkillType.TEST]: 1.0,
    [SkillType.GENERAL]: 1.0,
} as const;

/**
 * Calculate XP reward for a quiz question
 */
export const calculateQuizXP = (isCorrect: boolean): number => {
    return isCorrect ? XP_REWARDS.QUIZ_CORRECT : 0;
};

/**
 * Calculate XP reward for a perfect section (all quizzes correct)
 */
export const calculateSectionBonusXP = (correctAnswers: number, totalQuestions: number): number => {
    return correctAnswers === totalQuestions ? XP_REWARDS.QUIZ_PERFECT_SECTION : 0;
};

/**
 * Calculate XP reward for completed assignment based on score
 */
export const calculateAssignmentXP = (
    score: number,
    skill: SkillType,
    wordCount: number = 0
): number => {
    let baseXP: number = XP_REWARDS.ASSIGNMENT_BASE;

    // Bonus XP for high scores
    if (score >= 70) {
        const bonusPoints = Math.floor((score - 70) / 10);
        baseXP += bonusPoints * XP_REWARDS.ASSIGNMENT_BONUS_PER_10_POINTS;
    }

    // Apply skill weight multiplier
    const skillWeight = SKILL_XP_WEIGHTS[skill] || 1.0;
    baseXP = Math.floor(baseXP * skillWeight);

    // Small bonus for longer writing assignments
    if (skill === SkillType.WRITING && wordCount > 100) {
        baseXP += Math.floor((wordCount - 100) / 20) * 5; // 5 XP per 20 words over 100
    }

    return baseXP;
};

/**
 * Update user stats after task completion
 */
export const updateStatsAfterTask = (
    currentStats: UserStats,
    task: LearningTask,
    evaluation: AssignmentEvaluation,
    wordCount: number = 0
): UserStats => {
    const xpEarned = calculateAssignmentXP(evaluation.score, task.skill, wordCount);

    // Update skill-specific level
    const skillProgress = Math.min(100, currentStats.skillLevels[task.skill] + Math.floor(evaluation.score / 20));

    return {
        ...currentStats,
        totalXp: currentStats.totalXp + xpEarned,
        lessonsCompleted: currentStats.lessonsCompleted + 1,
        wordsWritten: currentStats.wordsWritten + wordCount,
        skillLevels: {
            ...currentStats.skillLevels,
            [task.skill]: skillProgress,
        },
    };
};

/**
 * Add XP for vocabulary word added
 */
export const addVocabularyXP = (currentStats: UserStats): UserStats => {
    return {
        ...currentStats,
        totalXp: currentStats.totalXp + XP_REWARDS.VOCABULARY_WORD,
    };
};

/**
 * Update streak and add streak bonus if applicable
 */
export const updateStreak = (currentStats: UserStats, lastActiveDate: string | null): UserStats => {
    const today = new Date().toISOString().split('T')[0];

    if (!lastActiveDate) {
        // First activity
        return {
            ...currentStats,
            streakDays: 1,
        };
    }

    const lastDate = new Date(lastActiveDate);
    const todayDate = new Date(today);
    const diffDays = Math.floor((todayDate.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
        // Same day, no change
        return currentStats;
    } else if (diffDays === 1) {
        // Consecutive day, increment streak and add bonus
        return {
            ...currentStats,
            streakDays: currentStats.streakDays + 1,
            totalXp: currentStats.totalXp + XP_REWARDS.STREAK_BONUS,
        };
    } else {
        // Streak broken, reset to 1
        return {
            ...currentStats,
            streakDays: 1,
        };
    }
};

/**
 * Calculate level based on total XP (simple linear progression)
 */
export const calculateLevel = (totalXp: number): number => {
    return Math.floor(totalXp / 500) + 1;
};

/**
 * Calculate XP needed for next level
 */
export const getXPForNextLevel = (currentLevel: number): number => {
    return currentLevel * 500;
};

/**
 * Get XP progress percentage towards next level
 */
export const getLevelProgress = (totalXp: number): { currentLevel: number; currentLevelXP: number; nextLevelXP: number; percentage: number } => {
    const currentLevel = calculateLevel(totalXp);
    const xpForCurrentLevel = (currentLevel - 1) * 500;
    const xpForNextLevel = getXPForNextLevel(currentLevel);
    const currentLevelXP = totalXp - xpForCurrentLevel;
    const percentage = (currentLevelXP / 500) * 100;

    return {
        currentLevel,
        currentLevelXP,
        nextLevelXP: xpForNextLevel,
        percentage: Math.min(100, percentage),
    };
};
