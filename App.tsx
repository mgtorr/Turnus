import React, { useState, useCallback, useEffect } from 'react';
import type { UserProfile, LearningPlan, CalendarEvent, UserStats, LearningTask, LessonContent, VocabularyItem, DailyChallenge } from './types';
import { SkillType } from './types';
import { MOCK_ACHIEVEMENTS } from './constants';
import GoalSetter from './components/GoalSetter';
import Dashboard from './components/Dashboard';
import LearningCalendar from './components/LearningCalendar';
import ChatTutor from './components/ChatTutor';
import ProfilePage from './components/ProfilePage';
import { generateLearningPlan, generateInteractiveLesson, generateVocabularyDefinition, generateDailyChallenge } from './services/geminiService';
import VocabularyVault from './components/VocabularyVault';
import TaskModal from './components/TaskModal';
import GlassToast from './components/ui/GlassToast';
import { useToast } from './hooks/useToast';
import AppLayout from './components/layout/AppLayout';
import Background from './components/layout/Background';
import GlassCard from './components/ui/GlassCard';
import {
    loadUserProfile,
    saveUserProfile,
    loadLearningPlan,
    saveLearningPlan,
    loadCalendarEvents,
    saveCalendarEvents,
    loadVocabulary,
    saveVocabulary,
    loadUserStats,
    saveUserStats,
    loadDailyChallenge,
    saveDailyChallenge
} from './utils/storage';
import { addVocabularyXP, updateStreak } from './utils/progressTracking';

type View = 'dashboard' | 'calendar' | 'tutor' | 'profile' | 'vocabulary';

// Loading Spinner Component
const Spinner: React.FC = () => (
    <div className="relative">
        <div className="w-16 h-16 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
        <div
            className="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-teal-500/50 rounded-full animate-spin"
            style={{ animationDuration: '3s', animationDirection: 'reverse' }}
        />
    </div>
);

const App: React.FC = () => {
    const { toasts, removeToast, showSuccess, showError, showInfo } = useToast();

    // Initialize state from localStorage
    const [userProfile, setUserProfile] = useState<UserProfile | null>(() => loadUserProfile());
    const [learningPlan, setLearningPlan] = useState<LearningPlan | null>(() => loadLearningPlan());
    const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>(() => loadCalendarEvents());
    const [vocabulary, setVocabulary] = useState<VocabularyItem[]>(() => loadVocabulary());
    const [dailyChallenge, setDailyChallenge] = useState<DailyChallenge | null>(() => loadDailyChallenge());
    const [isLoading, setIsLoading] = useState(false);
    const [activeView, setActiveView] = useState<View>('dashboard');

    // Task Modal State
    const [selectedTask, setSelectedTask] = useState<LearningTask | null>(null);
    const [lessonContent, setLessonContent] = useState<LessonContent | null>(null);
    const [isLoadingContent, setIsLoadingContent] = useState(false);

    // Initialize stats from localStorage or use defaults
    const [userStats, setUserStats] = useState<UserStats>(() => {
        const savedStats = loadUserStats();
        return savedStats || {
            totalXp: 0,
            streakDays: 0,
            lessonsCompleted: 0,
            wordsWritten: 0,
            skillLevels: {
                [SkillType.WRITING]: 0,
                [SkillType.ORAL]: 0,
                [SkillType.TEST]: 0,
                [SkillType.GENERAL]: 0
            },
            achievements: MOCK_ACHIEVEMENTS,
            certificates: []
        };
    });

    // Persist state to localStorage whenever it changes
    useEffect(() => {
        saveUserProfile(userProfile);
    }, [userProfile]);

    useEffect(() => {
        saveLearningPlan(learningPlan);
    }, [learningPlan]);

    useEffect(() => {
        saveCalendarEvents(calendarEvents);
    }, [calendarEvents]);

    useEffect(() => {
        saveVocabulary(vocabulary);
    }, [vocabulary]);

    useEffect(() => {
        saveUserStats(userStats);
    }, [userStats]);

    useEffect(() => {
        saveDailyChallenge(dailyChallenge);
    }, [dailyChallenge]);

    const handleProfileCreate = useCallback(async (profile: UserProfile) => {
        setIsLoading(true);
        try {
            const plan = await generateLearningPlan(profile);
            const challenge = await generateDailyChallenge(profile);

            setUserProfile(profile);
            setLearningPlan(plan);
            setDailyChallenge({
                id: Date.now().toString(),
                date: new Date().toISOString().split('T')[0],
                ...challenge,
                completed: false
            });

            // Populate calendar with initial plan
            const today = new Date();
            const initialEvents = plan.tasks.map((task, index) => {
                const eventDate = new Date(today);
                eventDate.setDate(today.getDate() + Math.floor(index / 2));
                return {
                    id: `${Date.now()}-${index}`,
                    title: task.topic,
                    date: eventDate.toISOString().split('T')[0],
                    skill: task.skill,
                    description: task.description,
                    durationMinutes: task.durationMinutes
                };
            });
            setCalendarEvents(initialEvents);
            showSuccess('Your personalized learning plan is ready!');
        } catch (error) {
            console.error(error);
            showError('Failed to create learning plan. Please try again.');
        } finally {
            setIsLoading(false);
        }
    }, [showSuccess, showError]);

    const addCalendarEvent = (event: CalendarEvent) => {
        setCalendarEvents(prev => [...prev, event]);
    };

    const handleTaskClick = async (task: LearningTask) => {
        if (!userProfile) return;

        setSelectedTask(task);
        setIsLoadingContent(true);
        setLessonContent(null);

        try {
            const content = await generateInteractiveLesson(task, userProfile);
            setLessonContent(content);
        } catch (error) {
            console.error("Failed to fetch task content", error);
        } finally {
            setIsLoadingContent(false);
        }
    };

    const handleAddWord = async (word: string) => {
        if (!userProfile) return;
        try {
            const def = await generateVocabularyDefinition(word, userProfile.language);
            const newItem: VocabularyItem = {
                id: Date.now().toString(),
                word,
                savedAt: new Date().toISOString(),
                masteryLevel: 0,
                ...def
            };
            setVocabulary(prev => [newItem, ...prev]);

            // Award XP for adding vocabulary
            const updatedStats = addVocabularyXP(userStats);
            setUserStats(updatedStats);

            showSuccess(`"${word}" added! +15 XP`);
        } catch (error) {
            console.error("Failed to add word", error);
            showError('Failed to add word. Please try again.');
        }
    };

    const handleCloseModal = () => {
        setSelectedTask(null);
        setLessonContent(null);
    };

    // Loading screen with glass effect
    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Background />
                <GlassCard className="text-center max-w-md">
                    <div className="flex flex-col items-center space-y-6">
                        <Spinner />
                        <div>
                            <h2 className="text-2xl font-bold text-[#f0f9ff] mb-2">
                                Designing Your Journey
                            </h2>
                            <p className="text-[#94a3b8]">
                                Our AI is crafting your personalized curriculum...
                            </p>
                        </div>
                    </div>
                </GlassCard>
            </div>
        );
    }

    // Onboarding screen
    if (!userProfile || !learningPlan) {
        return <GoalSetter onProfileCreate={handleProfileCreate} showWarning={showInfo} />;
    }

    // Main app with new layout
    return (
        <>
            <AppLayout
                activeView={activeView}
                onViewChange={setActiveView}
                userName={userProfile.name}
                userLanguage={userProfile.language}
                userLevel={userProfile.level}
            >
                <div className="space-y-8 pb-24 lg:pb-12">
                    {activeView === 'dashboard' && (
                        <Dashboard
                            userProfile={userProfile}
                            learningPlan={learningPlan}
                            dailyChallenge={dailyChallenge}
                            onPlanUpdate={setLearningPlan}
                            onTaskClick={handleTaskClick}
                        />
                    )}
                    {activeView === 'calendar' && (
                        <LearningCalendar
                            events={calendarEvents}
                            addEvent={addCalendarEvent}
                            onTaskClick={handleTaskClick}
                        />
                    )}
                    {activeView === 'vocabulary' && (
                        <VocabularyVault
                            vocabulary={vocabulary}
                            onAddWord={handleAddWord}
                        />
                    )}
                    {activeView === 'tutor' && <ChatTutor userId={userProfile.name} />}
                    {activeView === 'profile' && <ProfilePage userProfile={userProfile} stats={userStats} />}
                </div>
            </AppLayout>

            {/* Global Task Modal */}
            {selectedTask && (
                <TaskModal
                    task={selectedTask}
                    userProfile={userProfile}
                    lessonContent={lessonContent}
                    learningPlan={learningPlan}
                    userStats={userStats}
                    isLoading={isLoadingContent}
                    onClose={handleCloseModal}
                    onPlanUpdate={setLearningPlan}
                    onStatsUpdate={setUserStats}
                    showToast={(msg, type) => {
                        if (type === 'success') showSuccess(msg);
                        else if (type === 'error') showError(msg);
                        else showInfo(msg);
                    }}
                />
            )}

            {/* Toast Notifications */}
            <GlassToast toasts={toasts} onRemove={removeToast} />
        </>
    );
};

export default App;
