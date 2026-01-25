import React, { useState } from 'react';
import type { LearningTask, LessonContent, AssignmentEvaluation, UserProfile, LearningPlan, UserStats } from '../types';
import { SKILL_COLORS_GLASS } from '../styles/theme';
import { cn } from '../lib/utils';
import Certificate from './common/Certificate';
import GlassButton from './ui/GlassButton';
import { evaluateAssignment, readaptLearningPlan } from '../services/geminiService';
import { calculateQuizXP, calculateAssignmentXP, updateStatsAfterTask } from '../utils/progressTracking';

interface TaskModalProps {
    task: LearningTask;
    userProfile: UserProfile;
    lessonContent: LessonContent | null;
    learningPlan: LearningPlan;
    userStats: UserStats;
    isLoading: boolean;
    onClose: () => void;
    onPlanUpdate: (plan: LearningPlan) => void;
    onStatsUpdate: (stats: UserStats) => void;
    showToast?: (message: string, type: 'success' | 'info' | 'error') => void;
}

const TaskModal: React.FC<TaskModalProps> = ({
    task,
    userProfile,
    lessonContent,
    learningPlan,
    userStats,
    isLoading,
    onClose,
    onPlanUpdate,
    onStatsUpdate,
    showToast
}) => {
    const [step, setStep] = useState(0);
    const [showQuiz, setShowQuiz] = useState(false);
    const [quizAnswer, setQuizAnswer] = useState<number | null>(null);
    const [quizSubmitted, setQuizSubmitted] = useState(false);
    // const [correctQuizzes, setCorrectQuizzes] = useState(0); // Track correct answers

    const [assignmentText, setAssignmentText] = useState('');
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [evaluation, setEvaluation] = useState<AssignmentEvaluation | null>(null);

    const [isAdaptingPlan, setIsAdaptingPlan] = useState(false);
    const [planAdapted, setPlanAdapted] = useState(false);

    if (!task) return null;

    const currentSection = lessonContent?.sections[step];
    const isAssignmentStep = lessonContent && step === lessonContent.sections.length;

    const handleNext = () => {
        if (showQuiz && !quizSubmitted) return;
        setStep(prev => prev + 1);
        setShowQuiz(false);
        setQuizAnswer(null);
        setQuizSubmitted(false);
    };

    const handleCheckQuiz = () => {
        if (currentSection?.quiz && quizAnswer !== null) {
            const isCorrect = quizAnswer === currentSection.quiz.correctOptionIndex;

            // Award XP for correct answer
            if (isCorrect) {
                const xpEarned = calculateQuizXP(true);
                onStatsUpdate({
                    ...userStats,
                    totalXp: userStats.totalXp + xpEarned
                });
                // setCorrectQuizzes(prev => prev + 1);

                if (showToast) {
                    showToast(`+${xpEarned} XP! Great job!`, 'success');
                }
            }
        }
        setQuizSubmitted(true);
    };

    const submitAssignment = async () => {
        if (!lessonContent || assignmentText.trim().split(/\s+/).length < lessonContent.finalAssignment.minimumWordCount) {
            if (showToast) {
                showToast(`Please write at least ${lessonContent?.finalAssignment.minimumWordCount} words.`, 'info');
            } else {
                alert(`Please write at least ${lessonContent?.finalAssignment.minimumWordCount} words.`);
            }
            return;
        }

        setIsEvaluating(true);
        try {
            const result = await evaluateAssignment(task, assignmentText, userProfile.language);
            setEvaluation(result);

            // Calculate and award XP based on assignment score
            const wordCount = assignmentText.trim().split(/\s+/).length;
            const updatedStats = updateStatsAfterTask(userStats, task, result, wordCount);
            onStatsUpdate(updatedStats);

            // Calculate XP earned to show in toast
            const xpEarned = calculateAssignmentXP(result.score, task.skill, wordCount);

            if (showToast) {
                if (result.passed) {
                    showToast(`Assignment completed! +${xpEarned} XP earned!`, 'success');
                } else {
                    showToast(`Keep practicing! +${Math.floor(xpEarned / 2)} XP for effort.`, 'info');
                }
            }
        } catch (e) {
            console.error(e);
            if (showToast) {
                showToast('Error submitting assignment. Please try again.', 'error');
            } else {
                alert("Error submitting assignment. Please try again.");
            }
        } finally {
            setIsEvaluating(false);
        }
    };

    const handleAdaptPlan = async () => {
        if (!evaluation) return;
        setIsAdaptingPlan(true);
        try {
            const newPlan = await readaptLearningPlan(learningPlan, task, evaluation, userProfile);
            onPlanUpdate(newPlan);
            setPlanAdapted(true);
        } catch (e) {
            console.error("Failed to adapt plan", e);
        } finally {
            setIsAdaptingPlan(false);
        }
    };

    const renderProgressDots = () => {
        if (!lessonContent) return null;
        const totalSteps = lessonContent.sections.length + 1;

        return (
            <div className="flex items-center justify-center gap-2 py-4">
                {Array.from({ length: totalSteps }).map((_, idx) => (
                    <div
                        key={idx}
                        className={cn(
                            'w-2.5 h-2.5 rounded-full transition-all duration-300',
                            idx < step
                                ? 'bg-gradient-to-r from-cyan-500 to-teal-500 shadow-lg shadow-cyan-500/50'
                                : idx === step
                                    ? 'bg-gradient-to-r from-cyan-400 to-teal-400 w-8 shadow-lg shadow-cyan-500/50'
                                    : 'bg-[rgba(56,189,248,0.2)]'
                        )}
                    />
                ))}
            </div>
        );
    };

    const skillClass = SKILL_COLORS_GLASS[task.skill as keyof typeof SKILL_COLORS_GLASS] || SKILL_COLORS_GLASS['General Study'];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop with blur */}
            <div
                className="absolute inset-0 bg-[#030712]/80 backdrop-blur-xl"
                onClick={onClose}
            />

            {/* Modal container */}
            <div className={cn(
                'relative w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden',
                'bg-gradient-to-br from-[rgba(14,36,64,0.9)] to-[rgba(14,36,64,0.7)]',
                'backdrop-blur-2xl',
                'rounded-3xl',
                'border border-[rgba(56,189,248,0.2)]',
                'shadow-2xl shadow-black/50',
                'animate-fade-in-up'
            )}>
                {/* Decorative glow */}
                <div className="absolute -top-32 -right-32 w-64 h-64 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none" />
                <div className="absolute -bottom-32 -left-32 w-64 h-64 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

                {/* Header */}
                <div className="relative p-8 border-b border-[rgba(56,189,248,0.1)] flex justify-between items-start shrink-0">
                    <div className="pr-8">
                        <span className={cn(
                            'inline-flex items-center px-3 py-1 rounded-full text-xs font-bold mb-3',
                            'border backdrop-blur-sm',
                            skillClass
                        )}>
                            {task.skill}
                        </span>
                        <h2 className="text-3xl font-black text-[#f0f9ff] leading-tight tracking-tight">{task.topic}</h2>
                        {!isLoading && !evaluation && (
                            <div className="flex items-center gap-2 mt-3 text-sm font-medium text-[#94a3b8]">
                                <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
                                {isAssignmentStep ? "Final Challenge" : `Interactive Lesson • Part ${step + 1}/${lessonContent?.sections.length}`}
                            </div>
                        )}
                    </div>
                    <button
                        onClick={onClose}
                        className={cn(
                            'p-2.5 rounded-xl transition-all duration-200',
                            'bg-[rgba(14,36,64,0.5)] border border-[rgba(56,189,248,0.1)]',
                            'text-[#94a3b8] hover:text-[#f0f9ff]',
                            'hover:bg-[rgba(14,36,64,0.8)] hover:border-[rgba(56,189,248,0.3)]'
                        )}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {renderProgressDots()}

                {/* Content Area */}
                <div className="relative flex-1 overflow-y-auto p-8 custom-scrollbar">
                    {isLoading ? (
                        <div className="flex flex-col items-center justify-center h-full min-h-[300px] space-y-6">
                            <div className="relative">
                                <div className="w-16 h-16 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
                                <div className="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-teal-500/50 rounded-full animate-spin-slow" />
                            </div>
                            <p className="text-xl font-medium text-gradient animate-pulse">Generating your lesson...</p>
                        </div>
                    ) : evaluation ? (
                        // Result / Certificate View
                        <div className="animate-fade-in">
                            {evaluation.passed && evaluation.score >= 90 ? (
                                <div className="flex flex-col items-center justify-center min-h-[50vh]">
                                    <div className="mb-8 text-center">
                                        <h3 className="text-4xl font-black text-gradient mb-2">Mastery Achieved!</h3>
                                        <p className="text-[#94a3b8]">Perfect score of {evaluation.score}/100.</p>
                                    </div>
                                    <div className="transform scale-90 md:scale-100 origin-top hover:scale-[1.02] transition-transform duration-500">
                                        <Certificate
                                            userName={userProfile.name}
                                            courseName={task.topic}
                                            language={userProfile.language}
                                            date={new Date().toLocaleDateString()}
                                        />
                                    </div>
                                </div>
                            ) : (
                                <div className="max-w-3xl mx-auto">
                                    {/* Score Display */}
                                    <div className="text-center mb-10">
                                        <div className={cn(
                                            'w-32 h-32 rounded-full flex items-center justify-center mx-auto mb-6',
                                            'border-4 text-4xl font-black',
                                            'bg-gradient-to-br from-[rgba(14,36,64,0.8)] to-[rgba(14,36,64,0.5)]',
                                            'backdrop-blur-xl',
                                            evaluation.passed
                                                ? 'border-emerald-500/50 text-emerald-400 shadow-lg shadow-emerald-500/30'
                                                : 'border-amber-500/50 text-amber-400 shadow-lg shadow-amber-500/30'
                                        )}>
                                            {evaluation.score}
                                        </div>
                                        <h3 className={cn(
                                            'text-3xl font-bold mb-3',
                                            evaluation.passed ? 'text-emerald-400' : 'text-amber-400'
                                        )}>
                                            {evaluation.passed ? "Well Done!" : "Keep Pushing!"}
                                        </h3>
                                        <p className="text-lg text-[#94a3b8] max-w-xl mx-auto leading-relaxed">
                                            {evaluation.feedback}
                                        </p>
                                    </div>

                                    {/* Strengths & Improvements */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                                        <div className={cn(
                                            'p-6 rounded-2xl',
                                            'bg-gradient-to-br from-emerald-500/10 to-emerald-500/5',
                                            'border border-emerald-500/20',
                                            'backdrop-blur-xl'
                                        )}>
                                            <h4 className="font-bold text-emerald-400 mb-4 flex items-center uppercase tracking-wide text-sm">
                                                <span className="bg-emerald-500/20 rounded-lg p-1.5 mr-2">
                                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                                    </svg>
                                                </span>
                                                Strengths
                                            </h4>
                                            <ul className="space-y-3">
                                                {evaluation.strengths.map((s, i) => (
                                                    <li key={i} className="text-sm text-[#f0f9ff] flex items-start">
                                                        <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full mt-1.5 mr-2 shrink-0" />
                                                        {s}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>

                                        <div className={cn(
                                            'p-6 rounded-2xl',
                                            'bg-gradient-to-br from-amber-500/10 to-amber-500/5',
                                            'border border-amber-500/20',
                                            'backdrop-blur-xl'
                                        )}>
                                            <h4 className="font-bold text-amber-400 mb-4 flex items-center uppercase tracking-wide text-sm">
                                                <span className="bg-amber-500/20 rounded-lg p-1.5 mr-2">
                                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                                                    </svg>
                                                </span>
                                                Areas to Improve
                                            </h4>
                                            <ul className="space-y-3">
                                                {evaluation.weaknesses.map((w, i) => (
                                                    <li key={i} className="text-sm text-[#f0f9ff] flex items-start">
                                                        <span className="w-1.5 h-1.5 bg-amber-400 rounded-full mt-1.5 mr-2 shrink-0" />
                                                        {w}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>

                                    {/* AI Recommendation */}
                                    <div className={cn(
                                        'p-6 rounded-2xl mb-8',
                                        'bg-gradient-to-br from-cyan-500/10 to-teal-500/10',
                                        'border border-cyan-500/20',
                                        'backdrop-blur-xl'
                                    )}>
                                        <h4 className="font-bold text-cyan-400 mb-2 uppercase text-xs tracking-wider">AI Recommendation</h4>
                                        <p className="text-[#f0f9ff] text-base italic">"{evaluation.recommendation}"</p>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-6 border-t border-[rgba(56,189,248,0.1)]">
                                        <GlassButton
                                            variant="ghost"
                                            onClick={() => { setEvaluation(null); setIsEvaluating(false); }}
                                        >
                                            Review My Answer
                                        </GlassButton>

                                        {planAdapted ? (
                                            <span className={cn(
                                                'px-4 py-2.5 rounded-xl font-bold flex items-center',
                                                'bg-emerald-500/20 border border-emerald-500/30',
                                                'text-emerald-400'
                                            )}>
                                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                                </svg>
                                                Learning Plan Optimized
                                            </span>
                                        ) : (
                                            <GlassButton
                                                variant="primary"
                                                onClick={handleAdaptPlan}
                                                loading={isAdaptingPlan}
                                            >
                                                {isAdaptingPlan ? 'Updating Schedule...' : 'Adapt Plan Based on Results'}
                                            </GlassButton>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : isAssignmentStep && lessonContent ? (
                        <div className="max-w-3xl mx-auto animate-fade-in">
                            {/* Challenge Instructions */}
                            <div className={cn(
                                'p-8 mb-8 rounded-2xl relative overflow-hidden',
                                'bg-gradient-to-br from-violet-500/15 to-purple-500/10',
                                'border border-violet-500/20',
                                'backdrop-blur-xl'
                            )}>
                                {/* Decorative glow */}
                                <div className="absolute top-0 right-0 w-32 h-32 bg-violet-500/20 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none" />

                                <h3 className="text-xl font-bold text-violet-300 mb-4 relative z-10">Challenge Instructions</h3>
                                <div
                                    className="text-[#f0f9ff] prose-sm prose-invert max-w-none relative z-10 [&>p]:leading-relaxed [&>ul]:space-y-2 [&>ol]:space-y-2"
                                    dangerouslySetInnerHTML={{ __html: lessonContent.finalAssignment.instructions }}
                                />
                                <div className="mt-4 flex items-center text-xs font-bold text-violet-400 uppercase tracking-wide relative z-10">
                                    <span className="w-1.5 h-1.5 bg-violet-400 rounded-full mr-2" />
                                    Target: {lessonContent.finalAssignment.minimumWordCount}+ Words
                                </div>
                            </div>

                            {/* Glass Textarea */}
                            <textarea
                                value={assignmentText}
                                onChange={(e) => setAssignmentText(e.target.value)}
                                className={cn(
                                    'w-full h-64 p-6 mb-6 rounded-2xl resize-none',
                                    'bg-[rgba(14,36,64,0.5)]',
                                    'border border-[rgba(56,189,248,0.15)]',
                                    'text-[#f0f9ff] text-lg leading-relaxed',
                                    'placeholder-[#64748b]',
                                    'focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20',
                                    'transition-all duration-200'
                                )}
                                placeholder="Start writing your response here..."
                            />

                            {/* Word count indicator */}
                            <div className="flex justify-between items-center mb-6 text-sm text-[#64748b]">
                                <span>
                                    {assignmentText.trim().split(/\s+/).filter(w => w).length} / {lessonContent.finalAssignment.minimumWordCount}+ words
                                </span>
                                {assignmentText.trim().split(/\s+/).filter(w => w).length >= lessonContent.finalAssignment.minimumWordCount && (
                                    <span className="text-emerald-400 flex items-center gap-1">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                        </svg>
                                        Minimum reached
                                    </span>
                                )}
                            </div>

                            {isEvaluating ? (
                                <div className="flex flex-col items-center justify-center space-y-3 py-4">
                                    <div className="relative">
                                        <div className="w-10 h-10 border-3 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin" />
                                    </div>
                                    <span className="text-cyan-400 font-medium animate-pulse">Analyzing your proficiency...</span>
                                </div>
                            ) : (
                                <GlassButton
                                    variant="primary"
                                    size="lg"
                                    onClick={submitAssignment}
                                    className="w-full"
                                >
                                    Submit Assignment
                                </GlassButton>
                            )}
                        </div>
                    ) : currentSection ? (
                        <div className="max-w-3xl mx-auto animate-fade-in">
                            <h3 className="text-3xl font-bold text-[#f0f9ff] mb-8 pb-4 border-b border-[rgba(56,189,248,0.1)]">
                                {currentSection.title}
                            </h3>

                            {!showQuiz ? (
                                <div>
                                    <div
                                        className={cn(
                                            'prose prose-lg prose-invert max-w-none mb-10',
                                            'prose-headings:text-cyan-400',
                                            'prose-p:text-[#94a3b8] prose-p:leading-relaxed',
                                            'prose-strong:text-[#f0f9ff]',
                                            'prose-ul:text-[#94a3b8] prose-ol:text-[#94a3b8]',
                                            'prose-li:marker:text-cyan-500',
                                            'prose-a:text-cyan-400 prose-a:no-underline hover:prose-a:underline',
                                            'prose-code:text-teal-400 prose-code:bg-[rgba(14,36,64,0.5)] prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded'
                                        )}
                                        dangerouslySetInnerHTML={{ __html: currentSection.contentHtml }}
                                    />
                                    <div className="flex justify-end pt-4">
                                        {currentSection.quiz ? (
                                            <GlassButton
                                                variant="secondary"
                                                onClick={() => setShowQuiz(true)}
                                                icon={
                                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z" clipRule="evenodd" />
                                                    </svg>
                                                }
                                            >
                                                Take Quick Quiz
                                            </GlassButton>
                                        ) : (
                                            <GlassButton
                                                variant="primary"
                                                onClick={handleNext}
                                                icon={
                                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                                                    </svg>
                                                }
                                            >
                                                Next Section
                                            </GlassButton>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                // Quiz View with Glass Styling
                                <div className={cn(
                                    'p-8 rounded-3xl',
                                    'bg-gradient-to-br from-[rgba(14,36,64,0.8)] to-[rgba(14,36,64,0.5)]',
                                    'border border-[rgba(56,189,248,0.2)]',
                                    'backdrop-blur-xl',
                                    'shadow-2xl shadow-black/30'
                                )}>
                                    <span className="text-xs font-black text-cyan-400 uppercase tracking-widest mb-3 block">Quiz Time</span>
                                    <h4 className="text-2xl font-bold text-[#f0f9ff] mb-6">{currentSection.quiz?.question}</h4>

                                    {/* Quiz Options with Glass Radio Buttons */}
                                    <div className="space-y-4 mb-8">
                                        {currentSection.quiz?.options.map((option, idx) => (
                                            <button
                                                key={idx}
                                                onClick={() => !quizSubmitted && setQuizAnswer(idx)}
                                                disabled={quizSubmitted}
                                                className={cn(
                                                    'w-full text-left p-5 rounded-xl border-2 transition-all duration-200 flex items-center justify-between',
                                                    'backdrop-blur-sm',
                                                    quizSubmitted
                                                        ? idx === currentSection.quiz!.correctOptionIndex
                                                            ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 shadow-lg shadow-emerald-500/20'
                                                            : idx === quizAnswer
                                                                ? 'bg-red-500/20 border-red-500/50 text-red-300'
                                                                : 'bg-[rgba(14,36,64,0.3)] border-transparent opacity-50 text-[#64748b]'
                                                        : idx === quizAnswer
                                                            ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300 shadow-lg shadow-cyan-500/20 scale-[1.01]'
                                                            : 'bg-[rgba(14,36,64,0.4)] border-[rgba(56,189,248,0.1)] text-[#f0f9ff] hover:border-[rgba(56,189,248,0.3)] hover:bg-[rgba(14,36,64,0.6)]'
                                                )}
                                            >
                                                <span className="font-medium text-lg">{option}</span>
                                                {quizSubmitted && idx === currentSection.quiz!.correctOptionIndex && (
                                                    <span className="bg-emerald-500 text-white rounded-full p-1">
                                                        <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                                                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                                        </svg>
                                                    </span>
                                                )}
                                            </button>
                                        ))}
                                    </div>

                                    <div className="flex items-center justify-between pt-4 border-t border-[rgba(56,189,248,0.1)]">
                                        <div className="flex-1 pr-4">
                                            {quizSubmitted && (
                                                <p className="text-sm text-[#94a3b8] animate-fade-in">
                                                    <strong className="text-[#f0f9ff] block mb-1">Why?</strong>
                                                    {currentSection.quiz?.explanation}
                                                </p>
                                            )}
                                        </div>

                                        <div className="shrink-0">
                                            {!quizSubmitted ? (
                                                <GlassButton
                                                    variant="primary"
                                                    onClick={handleCheckQuiz}
                                                    disabled={quizAnswer === null}
                                                >
                                                    Check Answer
                                                </GlassButton>
                                            ) : (
                                                <GlassButton
                                                    variant="primary"
                                                    onClick={handleNext}
                                                    icon={
                                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                                            <path fillRule="evenodd" d="M12.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                                                        </svg>
                                                    }
                                                >
                                                    Continue
                                                </GlassButton>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : null}
                </div>
            </div>
        </div>
    );
};

export default TaskModal;