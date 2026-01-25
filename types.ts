
export enum LanguageLevel {
    A1 = "A1 (Beginner)",
    A2 = "A2 (Elementary)",
    B1 = "B1 (Intermediate)",
    B2 = "B2 (Upper-Intermediate)",
    C1 = "C1 (Advanced)",
}

export enum LearningGoal {
    TRAVEL = "Travel",
    BUSINESS = "Business Communication",
    CERTIFICATION = "Certification (e.g., TOEFL, IELTS)",
    CONVERSATIONAL = "Conversational Fluency",
    ACADEMIC = "Academic Purposes",
}

export enum SkillType {
    WRITING = "Writing",
    ORAL = "Oral",
    TEST = "Test",
    GENERAL = "General Study"
}

export interface CalendarEvent {
    id: string;
    title: string;
    date: string; // YYYY-MM-DD format
    skill: SkillType;
    description?: string;
    durationMinutes?: number;
}

export interface UserProfile {
    name: string;
    language: string;
    level: LanguageLevel;
    goals: LearningGoal[];
}

export interface LearningTask {
    skill: SkillType;
    topic: string;
    description: string;
    durationMinutes: number;
}

export interface LearningPlan {
    weeklyFocus: string;
    tasks: LearningTask[];
}

export interface ChatMessage {
    role: 'user' | 'model';
    text: string;
}

// Interactive Lesson Types
export interface Quiz {
    question: string;
    options: string[];
    correctOptionIndex: number;
    explanation: string;
}

export interface LessonSection {
    title: string;
    contentHtml: string; // Educational content in HTML
    quiz?: Quiz; // Optional mini-test after the section
}

export interface FinalAssignment {
    instructions: string;
    minimumWordCount: number;
}

export interface LessonContent {
    sections: LessonSection[];
    finalAssignment: FinalAssignment;
}

export interface AssignmentEvaluation {
    passed: boolean;
    score: number; // 0-100
    feedback: string; // General summary
    strengths: string[]; // Specific achievements
    weaknesses: string[]; // Areas for improvement
    recommendation: string; // Actionable advice
}

export interface PronunciationFeedback {
    score: number; // 0-100
    intonation: string;
    rhythm: string;
    phonemes: string[]; // List of sounds to improve
    suggestion: string; // Actionable tip
}

// Profile & Gamification Types
export interface Achievement {
    id: string;
    title: string;
    description: string;
    icon: string; // Emoji or SVG path
    unlocked: boolean;
    unlockedAt?: Date;
}

export interface VocabularyItem {
    id: string;
    word: string;
    translation: string;
    definition: string;
    exampleSentence: string;
    savedAt: string; // ISO Date
    masteryLevel: number; // 0-100
}

export interface DailyChallenge {
    id: string;
    date: string; // YYYY-MM-DD
    title: string;
    description: string;
    task: LearningTask;
    completed: boolean;
    rewardXp: number;
}

export interface CertificateRecord {
    id: string;
    courseName: string;
    date: string;
    score: number;
}

export interface UserStats {
    totalXp: number;
    streakDays: number;
    lessonsCompleted: number;
    wordsWritten: number;
    skillLevels: Record<SkillType, number>; // 0-100 progress
    achievements: Achievement[];
    certificates: CertificateRecord[];
}