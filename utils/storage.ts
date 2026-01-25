import type { UserProfile, LearningPlan, CalendarEvent, VocabularyItem, UserStats, DailyChallenge } from '../types';

const STORAGE_KEYS = {
    USER_PROFILE: 'fluentflow_user_profile',
    LEARNING_PLAN: 'fluentflow_learning_plan',
    CALENDAR_EVENTS: 'fluentflow_calendar_events',
    VOCABULARY: 'fluentflow_vocabulary',
    USER_STATS: 'fluentflow_user_stats',
    DAILY_CHALLENGE: 'fluentflow_daily_challenge',
} as const;

// Generic storage utilities
export const saveToStorage = <T>(key: string, data: T): void => {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
        console.error(`Failed to save ${key} to localStorage:`, error);
    }
};

export const loadFromStorage = <T>(key: string): T | null => {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    } catch (error) {
        console.error(`Failed to load ${key} from localStorage:`, error);
        return null;
    }
};

export const removeFromStorage = (key: string): void => {
    try {
        localStorage.removeItem(key);
    } catch (error) {
        console.error(`Failed to remove ${key} from localStorage:`, error);
    }
};

// Specific data storage functions
export const saveUserProfile = (profile: UserProfile | null): void => {
    if (profile) {
        saveToStorage(STORAGE_KEYS.USER_PROFILE, profile);
    } else {
        removeFromStorage(STORAGE_KEYS.USER_PROFILE);
    }
};

export const loadUserProfile = (): UserProfile | null => {
    return loadFromStorage<UserProfile>(STORAGE_KEYS.USER_PROFILE);
};

export const saveLearningPlan = (plan: LearningPlan | null): void => {
    if (plan) {
        saveToStorage(STORAGE_KEYS.LEARNING_PLAN, plan);
    } else {
        removeFromStorage(STORAGE_KEYS.LEARNING_PLAN);
    }
};

export const loadLearningPlan = (): LearningPlan | null => {
    return loadFromStorage<LearningPlan>(STORAGE_KEYS.LEARNING_PLAN);
};

export const saveCalendarEvents = (events: CalendarEvent[]): void => {
    saveToStorage(STORAGE_KEYS.CALENDAR_EVENTS, events);
};

export const loadCalendarEvents = (): CalendarEvent[] => {
    return loadFromStorage<CalendarEvent[]>(STORAGE_KEYS.CALENDAR_EVENTS) || [];
};

export const saveVocabulary = (vocabulary: VocabularyItem[]): void => {
    saveToStorage(STORAGE_KEYS.VOCABULARY, vocabulary);
};

export const loadVocabulary = (): VocabularyItem[] => {
    return loadFromStorage<VocabularyItem[]>(STORAGE_KEYS.VOCABULARY) || [];
};

export const saveUserStats = (stats: UserStats): void => {
    saveToStorage(STORAGE_KEYS.USER_STATS, stats);
};

export const loadUserStats = (): UserStats | null => {
    return loadFromStorage<UserStats>(STORAGE_KEYS.USER_STATS);
};

export const saveDailyChallenge = (challenge: DailyChallenge | null): void => {
    if (challenge) {
        saveToStorage(STORAGE_KEYS.DAILY_CHALLENGE, challenge);
    } else {
        removeFromStorage(STORAGE_KEYS.DAILY_CHALLENGE);
    }
};

export const loadDailyChallenge = (): DailyChallenge | null => {
    return loadFromStorage<DailyChallenge>(STORAGE_KEYS.DAILY_CHALLENGE);
};

// Clear all app data
export const clearAllData = (): void => {
    Object.values(STORAGE_KEYS).forEach(key => {
        removeFromStorage(key);
    });
};
