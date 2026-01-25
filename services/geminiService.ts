import { GoogleGenAI, Type, GenerateContentResponse, Chat } from "@google/genai";
import type { UserProfile, LearningPlan, LearningTask, LessonContent, AssignmentEvaluation, PronunciationFeedback } from '../types';

if (!process.env.GEMINI_API_KEY) {
    throw new Error("GEMINI_API_KEY environment variable is not set.");
}

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

export const generateLearningPlan = async (profile: UserProfile): Promise<LearningPlan> => {
    const prompt = `
    Create a personalized one-week language learning plan for a user with the following profile:
    - Language: ${profile.language}
    - Proficiency Level: ${profile.level}
    - Primary Goals: ${profile.goals.join(", ")}

    The plan should include a weekly focus and a list of specific, actionable tasks.
    Each task should have a skill type (Writing, Oral, Test, General Study), a topic, a short description, and a recommended duration in minutes.
    Return the plan as a JSON object.
    `;

    try {
        const response: GenerateContentResponse = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        weeklyFocus: {
                            type: Type.STRING,
                            description: "A brief summary of the main goal for the week."
                        },
                        tasks: {
                            type: Type.ARRAY,
                            items: {
                                type: Type.OBJECT,
                                properties: {
                                    skill: { type: Type.STRING, enum: ["Writing", "Oral", "Test", "General Study"] },
                                    topic: { type: Type.STRING },
                                    description: { type: Type.STRING },
                                    durationMinutes: { type: Type.INTEGER }
                                },
                                required: ["skill", "topic", "description", "durationMinutes"]
                            }
                        }
                    },
                    required: ["weeklyFocus", "tasks"]
                }
            }
        });

        if (!response.text) {
            throw new Error("No text returned from Gemini");
        }
        const jsonText = response.text.trim();
        return JSON.parse(jsonText) as LearningPlan;

    } catch (error) {
        console.error("Error generating learning plan:", error);
        throw new Error("Failed to generate learning plan. Please check your API key and network connection.");
    }
};

export const generateInteractiveLesson = async (task: LearningTask, profile: UserProfile): Promise<LessonContent> => {
    const prompt = `
    Act as an expert language teacher. Create a structured, interactive lesson for:
    Language: ${profile.language} (${profile.level})
    Topic: ${task.topic}
    Description: ${task.description}

    Structure:
    1. Divide the lesson into 2-3 logical sections (e.g., Vocabulary, Grammar, Usage).
    2. For each section, provide:
       - 'title': Section title.
       - 'contentHtml': Educational explanation formatted in clean HTML (use <h3>, <p>, <ul>, <li>, <strong>, <em class="text-sky-600">).
       - 'quiz': A generic object with a 'question', 3-4 'options', the 'correctOptionIndex' (0-based), and a short 'explanation' for why it's correct.
    3. A 'finalAssignment':
       - 'instructions': Clear instructions for a writing or speaking task the user must perform to prove mastery. Format as HTML.
       - 'minimumWordCount': A reasonable number (e.g. 20-50).
    
    Return strictly JSON adhering to this structure.
    `;

    try {
        const response = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        sections: {
                            type: Type.ARRAY,
                            items: {
                                type: Type.OBJECT,
                                properties: {
                                    title: { type: Type.STRING },
                                    contentHtml: { type: Type.STRING },
                                    quiz: {
                                        type: Type.OBJECT,
                                        properties: {
                                            question: { type: Type.STRING },
                                            options: { type: Type.ARRAY, items: { type: Type.STRING } },
                                            correctOptionIndex: { type: Type.INTEGER },
                                            explanation: { type: Type.STRING }
                                        },
                                        required: ["question", "options", "correctOptionIndex", "explanation"]
                                    }
                                },
                                required: ["title", "contentHtml", "quiz"]
                            }
                        },
                        finalAssignment: {
                            type: Type.OBJECT,
                            properties: {
                                instructions: { type: Type.STRING },
                                minimumWordCount: { type: Type.INTEGER }
                            },
                            required: ["instructions", "minimumWordCount"]
                        }
                    },
                    required: ["sections", "finalAssignment"]
                }
            }
        });
        if (!response.text) {
            throw new Error("No content generated");
        }
        return JSON.parse(response.text.trim()) as LessonContent;
    } catch (error) {
        console.error("Error generating lesson:", error);
        throw error;
    }
};

export const evaluateAssignment = async (
    task: LearningTask,
    userSubmission: string,
    targetLanguage: string
): Promise<AssignmentEvaluation> => {
    const prompt = `
    You are a strict but constructive language examiner. 
    Task: ${task.topic} - ${task.description}
    Target Language: ${targetLanguage}
    User Submission: "${userSubmission}"

    Evaluate the submission in detail.
    1. Determine if it meets the requirements.
    2. Assign a score (0-100). Pass mark is 70.
    3. Provide a general 'feedback' summary.
    4. List specific 'strengths' (what they did well).
    5. List specific 'weaknesses' (grammar errors, vocab misuse, etc.).
    6. Provide a 'recommendation' for what they should study next based on this result.

    Return JSON.
    `;

    try {
        const response = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        passed: { type: Type.BOOLEAN },
                        score: { type: Type.INTEGER },
                        feedback: { type: Type.STRING },
                        strengths: { type: Type.ARRAY, items: { type: Type.STRING } },
                        weaknesses: { type: Type.ARRAY, items: { type: Type.STRING } },
                        recommendation: { type: Type.STRING }
                    },
                    required: ["passed", "score", "feedback", "strengths", "weaknesses", "recommendation"]
                }
            }
        });
        if (!response.text) {
            throw new Error("Evaluation failed: No text returned");
        }
        return JSON.parse(response.text.trim()) as AssignmentEvaluation;
    } catch (error) {
        console.error("Error evaluating assignment:", error);
        return {
            passed: false,
            score: 0,
            feedback: "System error during evaluation.",
            strengths: [],
            weaknesses: [],
            recommendation: "Please try submitting again."
        };
    }
}

export const readaptLearningPlan = async (
    currentPlan: LearningPlan,
    completedTask: LearningTask,
    evaluation: AssignmentEvaluation,
    _profile: UserProfile
): Promise<LearningPlan> => {
    const prompt = `
    The user has just completed the task: "${completedTask.topic}".
    Score: ${evaluation.score}/100.
    Weaknesses identified: ${evaluation.weaknesses.join(", ")}.
    
    Current Weekly Focus: ${currentPlan.weeklyFocus}
    Current Tasks: ${JSON.stringify(currentPlan.tasks)}

    Please readapt the learning plan.
    - If the score is low or weaknesses are significant, replace some future tasks with review or practice exercises targeting those specific weaknesses.
    - If the score is high, perhaps advance the difficulty of remaining tasks slightly.
    - Keep the same "weeklyFocus".
    - Return the full updated plan in JSON format.
    `;

    try {
        const response = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        weeklyFocus: { type: Type.STRING },
                        tasks: {
                            type: Type.ARRAY,
                            items: {
                                type: Type.OBJECT,
                                properties: {
                                    skill: { type: Type.STRING, enum: ["Writing", "Oral", "Test", "General Study"] },
                                    topic: { type: Type.STRING },
                                    description: { type: Type.STRING },
                                    durationMinutes: { type: Type.INTEGER }
                                },
                                required: ["skill", "topic", "description", "durationMinutes"]
                            }
                        }
                    },
                    required: ["weeklyFocus", "tasks"]
                }
            }
        });
        if (!response.text) {
            return currentPlan;
        }
        return JSON.parse(response.text.trim()) as LearningPlan;
    } catch (error) {
        console.error("Error adapting plan:", error);
        return currentPlan; // Return original if failure
    }
};

export const createChatSession = (history: { role: string, parts: { text: string }[] }[] = []): Chat => {
    return ai.chats.create({
        model: 'gemini-2.5-flash',
        config: {
            systemInstruction: `You are an expert language tutor. Be patient, encouraging, and provide clear, concise feedback. 
            When the user makes a mistake, gently correct them and explain the rule. 
            Keep your responses focused on language learning. You can role-play scenarios if the user asks.`
        },
        history: history
    });
};

// Helper to create a WAV header for raw PCM data
const createWavHeader = (length: number, sampleRate: number = 16000, numChannels: number = 1): Uint8Array => {
    const buffer = new ArrayBuffer(44);
    const view = new DataView(buffer);

    // RIFF chunk descriptor
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + length, true);
    writeString(view, 8, 'WAVE');

    // fmt sub-chunk
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true); // Subchunk1Size (16 for PCM)
    view.setUint16(20, 1, true); // AudioFormat (1 for PCM)
    view.setUint16(22, numChannels, true); // NumChannels
    view.setUint32(24, sampleRate, true); // SampleRate
    view.setUint32(28, sampleRate * numChannels * 2, true); // ByteRate
    view.setUint16(32, numChannels * 2, true); // BlockAlign
    view.setUint16(34, 16, true); // BitsPerSample

    // data sub-chunk
    writeString(view, 36, 'data');
    view.setUint32(40, length, true);

    return new Uint8Array(buffer);
};

const writeString = (view: DataView, offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
};

export const analyzePronunciation = async (base64PcmAudio: string, language: string = "English"): Promise<PronunciationFeedback> => {
    // Convert raw base64 PCM to binary
    const binaryString = atob(base64PcmAudio);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }

    // Wrap in WAV header
    const header = createWavHeader(bytes.length);
    const wavBytes = new Uint8Array(header.length + bytes.length);
    wavBytes.set(header);
    wavBytes.set(bytes, header.length);

    // Convert back to base64 for the API
    let binary = '';
    for (let i = 0; i < wavBytes.byteLength; i++) {
        binary += String.fromCharCode(wavBytes[i]);
    }
    const base64Wav = btoa(binary);

    const prompt = `
    Analyze the pronunciation in this audio clip. The target language is ${language}.
    Focus on:
    1. Intonation and stress.
    2. Rhythm and fluency.
    3. Specific phonemes or sounds that were mispronounced.

    Provide constructive, actionable feedback in JSON format.
    `;

    try {
        const response = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: {
                parts: [
                    { inlineData: { mimeType: "audio/wav", data: base64Wav } },
                    { text: prompt }
                ]
            },
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        score: { type: Type.INTEGER, description: "Overall pronunciation score 0-100" },
                        intonation: { type: Type.STRING, description: "Feedback on pitch and stress patterns" },
                        rhythm: { type: Type.STRING, description: "Feedback on fluency and speed" },
                        phonemes: { type: Type.ARRAY, items: { type: Type.STRING }, description: "List of specific sounds to practice" },
                        suggestion: { type: Type.STRING, description: "One actionable tip for improvement" }
                    },
                    required: ["score", "intonation", "rhythm", "phonemes", "suggestion"]
                }
            }
        });

        if (!response.text) throw new Error("No analysis returned");
        return JSON.parse(response.text.trim()) as PronunciationFeedback;
    } catch (error) {
        console.error("Pronunciation analysis failed:", error);
        return {
            score: 0,
            intonation: "Could not analyze.",
            rhythm: "Could not analyze.",
            phonemes: [],
            suggestion: "Please try speaking clearly again."
        };
    }
};

export const generateVocabularyDefinition = async (word: string, language: string): Promise<{ translation: string; definition: string; exampleSentence: string }> => {
    const prompt = `
    Define the word "${word}" in ${language}.
    Return a JSON object with:
    - translation: English translation
    - definition: A simple definition in ${language}
    - exampleSentence: A sentence using the word in ${language}
    `;

    try {
        const response = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        translation: { type: Type.STRING },
                        definition: { type: Type.STRING },
                        exampleSentence: { type: Type.STRING }
                    },
                    required: ["translation", "definition", "exampleSentence"]
                }
            }
        });
        if (!response.text) throw new Error("No definition returned");
        return JSON.parse(response.text.trim());
    } catch (error) {
        console.error("Vocabulary definition failed:", error);
        throw error;
    }
};

export const generateDailyChallenge = async (profile: UserProfile): Promise<{ title: string; description: string; task: LearningTask; rewardXp: number }> => {
    const prompt = `
    Create a "Daily Challenge" for a ${profile.language} learner (${profile.level}).
    It should be a short, fun task.
    Return JSON with:
    - title
    - description
    - task: A LearningTask object (skill, topic, description, durationMinutes)
    - rewardXp: integer (e.g. 50-100)
    `;

    try {
        const response = await ai.models.generateContent({
            model: "gemini-2.5-flash",
            contents: prompt,
            config: {
                responseMimeType: "application/json",
                responseSchema: {
                    type: Type.OBJECT,
                    properties: {
                        title: { type: Type.STRING },
                        description: { type: Type.STRING },
                        task: {
                            type: Type.OBJECT,
                            properties: {
                                skill: { type: Type.STRING, enum: ["Writing", "Oral", "Test", "General Study"] },
                                topic: { type: Type.STRING },
                                description: { type: Type.STRING },
                                durationMinutes: { type: Type.INTEGER }
                            },
                            required: ["skill", "topic", "description", "durationMinutes"]
                        },
                        rewardXp: { type: Type.INTEGER }
                    },
                    required: ["title", "description", "task", "rewardXp"]
                }
            }
        });
        if (!response.text) throw new Error("No challenge generated");
        return JSON.parse(response.text.trim());
    } catch (error) {
        console.error("Daily challenge generation failed:", error);
        throw error;
    }
};