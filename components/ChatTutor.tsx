import React, { useState, useEffect, useRef, useCallback } from 'react';
import { GoogleGenAI, Modality, Chat, LiveServerMessage } from "@google/genai";
import type { ChatMessage, PronunciationFeedback } from '../types';
import { createChatSession, analyzePronunciation } from '../services/geminiService';
import GlassCard from './ui/GlassCard';
import GlassButton from './ui/GlassButton';
import GlassInput from './ui/GlassInput';
import { GlassTabs, GlassTabContent } from './ui/GlassTabs';
import { cn } from '../lib/utils';

// Audio utilities
const decode = (base64: string): Uint8Array => {
    const binaryString = atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes;
};

async function decodeAudioData(data: Uint8Array, ctx: AudioContext): Promise<AudioBuffer> {
    const dataInt16 = new Int16Array(data.buffer);
    const frameCount = dataInt16.length;
    const buffer = ctx.createBuffer(1, frameCount, 24000);
    const channelData = buffer.getChannelData(0);
    for (let i = 0; i < frameCount; i++) {
        channelData[i] = dataInt16[i] / 32768.0;
    }
    return buffer;
}

const encode = (bytes: Uint8Array): string => {
    let binary = '';
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
};

// Icons
const MicIcon = ({ className = "h-6 w-6" }: { className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
    </svg>
);

const WritingIcon = ({ className = "h-6 w-6" }: { className?: string }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.5L15.232 5.232z" />
    </svg>
);

// Spinner
const Spinner = () => (
    <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
);

interface ChatTutorProps {
    userId?: string;
}

const ChatTutor: React.FC<ChatTutorProps> = ({ userId = 'guest' }) => {
    const [mode, setMode] = useState<'writing' | 'oral'>('writing');
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const chatSession = useRef<Chat | null>(null);
    const chatContainerRef = useRef<HTMLDivElement>(null);

    // Oral practice state
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState<ChatMessage[]>([]);
    const [pronunciationFeedback, setPronunciationFeedback] = useState<PronunciationFeedback | null>(null);
    const [isAnalyzingAudio, setIsAnalyzingAudio] = useState(false);

    const sessionPromiseRef = useRef<Promise<any> | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const mediaStreamRef = useRef<MediaStream | null>(null);
    const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
    const nextStartTimeRef = useRef(0);
    const outputAudioContextRef = useRef<AudioContext | null>(null);
    const userAudioBufferRef = useRef<Int16Array[]>([]);

    const stopOralSession = useCallback(() => {
        if (!isListening) return;
        setIsListening(false);
        sessionPromiseRef.current?.then(session => session.close());
        sessionPromiseRef.current = null;
        scriptProcessorRef.current?.disconnect();
        scriptProcessorRef.current = null;
        mediaStreamRef.current?.getTracks().forEach(track => track.stop());
        mediaStreamRef.current = null;
        audioContextRef.current?.close();
        audioContextRef.current = null;
        outputAudioContextRef.current?.close();
        outputAudioContextRef.current = null;
        nextStartTimeRef.current = 0;
        userAudioBufferRef.current = [];
    }, [isListening]);

    useEffect(() => {
        if (mode === 'writing') {
            const storageKey = `fluentflow_chat_${userId}`;
            const savedHistory = localStorage.getItem(storageKey);

            let initialMessages: ChatMessage[] = [];
            let geminiHistory: any[] = [];

            if (savedHistory) {
                try {
                    const parsed = JSON.parse(savedHistory);
                    if (Array.isArray(parsed)) {
                        initialMessages = parsed;
                        geminiHistory = parsed.map(msg => ({
                            role: msg.role,
                            parts: [{ text: msg.text }]
                        }));
                    }
                } catch (e) {
                    console.error("Failed to parse saved chat history", e);
                }
            }

            chatSession.current = createChatSession(geminiHistory);

            if (initialMessages.length > 0) {
                setMessages(initialMessages);
            } else {
                setMessages([{ role: 'model', text: 'Hello! How can I help you with your language practice today?' }]);
            }
        } else {
            stopOralSession();
            setTranscript([]);
            setPronunciationFeedback(null);
        }
    }, [mode, userId, stopOralSession]);

    useEffect(() => {
        if (mode === 'writing' && messages.length > 0) {
            const storageKey = `fluentflow_chat_${userId}`;
            const validMessages = messages.filter(m => m.text.trim() !== '');
            localStorage.setItem(storageKey, JSON.stringify(validMessages));
        }
    }, [messages, mode, userId]);

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages, transcript]);

    const handleSendMessage = async () => {
        if (!input.trim() || !chatSession.current) return;

        const userMessage: ChatMessage = { role: 'user', text: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const stream = await chatSession.current.sendMessageStream({ message: input });
            let modelResponse = '';
            setMessages(prev => [...prev, { role: 'model', text: '' }]);

            for await (const chunk of stream) {
                modelResponse += chunk.text;
                setMessages(prev => {
                    const newMessages = [...prev];
                    newMessages[newMessages.length - 1].text = modelResponse;
                    return newMessages;
                });
            }
        } catch (error) {
            console.error("Error sending message:", error);
            setMessages(prev => [...prev, { role: 'model', text: 'Sorry, I encountered an error.' }]);
        } finally {
            setIsLoading(false);
        }
    };

    const triggerPronunciationAnalysis = async () => {
        if (userAudioBufferRef.current.length === 0) return;

        setIsAnalyzingAudio(true);
        const totalLength = userAudioBufferRef.current.reduce((acc, chunk) => acc + chunk.length, 0);
        const combinedBuffer = new Int16Array(totalLength);
        let offset = 0;
        for (const chunk of userAudioBufferRef.current) {
            combinedBuffer.set(chunk, offset);
            offset += chunk.length;
        }
        const base64Audio = encode(new Uint8Array(combinedBuffer.buffer));
        userAudioBufferRef.current = [];

        try {
            const feedback = await analyzePronunciation(base64Audio);
            setPronunciationFeedback(feedback);
        } catch (e) {
            console.error("Failed to analyze pronunciation", e);
        } finally {
            setIsAnalyzingAudio(false);
        }
    };

    const startOralSession = async () => {
        if (isListening) return;
        setPronunciationFeedback(null);
        userAudioBufferRef.current = [];

        try {
            const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
            const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext; // eslint-disable-line @typescript-eslint/no-explicit-any
            outputAudioContextRef.current = new AudioContextClass({ sampleRate: 24000 });
            audioContextRef.current = new AudioContextClass({ sampleRate: 16000 });

            setIsListening(true);
            setTranscript([{ role: 'model', text: 'Listening... Speak now!' }]);

            sessionPromiseRef.current = ai.live.connect({
                model: 'gemini-2.5-flash-native-audio-preview-09-2025',
                config: {
                    responseModalities: [Modality.AUDIO],
                    inputAudioTranscription: {},
                    outputAudioTranscription: {},
                    speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Zephyr' } } }
                },
                callbacks: {
                    onopen: async () => {
                        mediaStreamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
                        const source = audioContextRef.current!.createMediaStreamSource(mediaStreamRef.current);
                        scriptProcessorRef.current = audioContextRef.current!.createScriptProcessor(4096, 1, 1);

                        scriptProcessorRef.current.onaudioprocess = (event) => {
                            const inputData = event.inputBuffer.getChannelData(0);
                            const int16 = new Int16Array(inputData.length);
                            for (let i = 0; i < inputData.length; i++) {
                                int16[i] = inputData[i] * 32768;
                            }
                            userAudioBufferRef.current.push(new Int16Array(int16));
                            const base64 = encode(new Uint8Array(int16.buffer));
                            sessionPromiseRef.current?.then(session => session.sendRealtimeInput({ media: { data: base64, mimeType: 'audio/pcm;rate=16000' } }));
                        };
                        source.connect(scriptProcessorRef.current);
                        scriptProcessorRef.current.connect(audioContextRef.current!.destination);
                    },
                    onmessage: async (message: LiveServerMessage) => {
                        if (message.serverContent?.outputTranscription) {
                            setTranscript(prev => {
                                const last = prev[prev.length - 1];
                                if (last?.role === 'model') {
                                    const updated = { ...last, text: last.text + (message.serverContent!.outputTranscription?.text || '') };
                                    return [...prev.slice(0, -1), updated];
                                }
                                return [...prev, { role: 'model', text: message.serverContent!.outputTranscription?.text || '' }];
                            });
                        }
                        if (message.serverContent?.inputTranscription) {
                            setTranscript(prev => {
                                const last = prev[prev.length - 1];
                                if (last?.role === 'user') {
                                    const updated = { ...last, text: last.text + (message.serverContent!.inputTranscription?.text || '') };
                                    return [...prev.slice(0, -1), updated];
                                }
                                return [...prev, { role: 'user', text: message.serverContent!.inputTranscription?.text || '' }];
                            });
                        }

                        if (message.serverContent?.turnComplete) {
                            triggerPronunciationAnalysis();
                        }

                        const audioData = message.serverContent?.modelTurn?.parts?.[0]?.inlineData?.data;
                        if (audioData && outputAudioContextRef.current) {
                            if (userAudioBufferRef.current.length > 0) {
                                triggerPronunciationAnalysis();
                            }
                            const audioBuffer = await decodeAudioData(decode(audioData), outputAudioContextRef.current);
                            const source = outputAudioContextRef.current.createBufferSource();
                            source.buffer = audioBuffer;
                            source.connect(outputAudioContextRef.current.destination);
                            const now = outputAudioContextRef.current.currentTime;
                            const startTime = Math.max(now, nextStartTimeRef.current);
                            source.start(startTime);
                            nextStartTimeRef.current = startTime + audioBuffer.duration;
                        }
                    },
                    onclose: () => stopOralSession(),
                    onerror: (e) => {
                        console.error("Oral session error:", e);
                        stopOralSession();
                    },
                }
            });
        } catch (error) {
            console.error("Failed to start oral session:", error);
            setIsListening(false);
        }
    };



    const tabs = [
        { value: 'writing', label: 'Writing', icon: <WritingIcon className="w-4 h-4" /> },
        { value: 'oral', label: 'Oral', icon: <MicIcon className="w-4 h-4" /> },
    ];

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <header>
                <h1 className="text-4xl font-black text-[#f0f9ff] tracking-tight">
                    AI <span className="text-gradient">Tutor</span>
                </h1>
                <p className="text-[#94a3b8] mt-2">
                    Practice your language skills with our AI assistant.
                </p>
            </header>

            <GlassCard padding="none" className="flex flex-col h-[75vh] overflow-hidden">
                {/* Header Bar */}
                <div className="p-4 md:p-6 border-b border-[rgba(56,189,248,0.1)] flex justify-between items-center shrink-0 bg-[rgba(14,36,64,0.3)]">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 flex items-center justify-center text-white shadow-lg shadow-cyan-500/30">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                            </svg>
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-[#f0f9ff]">AI Tutor</h2>
                            <p className="text-xs text-[#64748b]">Always here to help</p>
                        </div>
                    </div>

                    {/* Mode Toggle */}
                    <div className="flex p-1 rounded-xl bg-[rgba(14,36,64,0.5)] border border-[rgba(56,189,248,0.1)]">
                        {tabs.map((tab) => (
                            <button
                                key={tab.value}
                                onClick={() => setMode(tab.value as 'writing' | 'oral')}
                                className={cn(
                                    'px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2',
                                    mode === tab.value
                                        ? 'bg-gradient-to-r from-[rgba(14,36,64,0.8)] to-[rgba(14,36,64,0.6)] text-cyan-400 shadow-lg border border-[rgba(56,189,248,0.2)]'
                                        : 'text-[#94a3b8] hover:text-[#f0f9ff]'
                                )}
                            >
                                {tab.icon}
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Chat Messages */}
                <div
                    ref={chatContainerRef}
                    className="flex-1 p-6 overflow-y-auto space-y-4 custom-scrollbar"
                >
                    {(mode === 'writing' ? messages : transcript).map((msg, index) => (
                        <div
                            key={index}
                            className={cn('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}
                        >
                            <div
                                className={cn(
                                    'max-w-[85%] md:max-w-[70%] px-5 py-4 rounded-2xl text-sm md:text-base',
                                    msg.role === 'user'
                                        ? [
                                            'bg-gradient-to-r from-cyan-500 to-teal-500',
                                            'text-white',
                                            'rounded-tr-sm',
                                            'shadow-lg shadow-cyan-500/20',
                                        ]
                                        : [
                                            'bg-[rgba(14,36,64,0.6)]',
                                            'border border-[rgba(56,189,248,0.15)]',
                                            'text-[#f0f9ff]',
                                            'rounded-tl-sm',
                                        ]
                                )}
                            >
                                {msg.text || (
                                    <div className="flex space-x-1 h-5 items-center">
                                        <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" />
                                        <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '75ms' }} />
                                        <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    {isLoading && mode === 'writing' && (
                        <div className="flex justify-start">
                            <div className="px-5 py-4 rounded-2xl rounded-tl-sm bg-[rgba(14,36,64,0.6)] border border-[rgba(56,189,248,0.15)]">
                                <div className="flex space-x-1 h-5 items-center">
                                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" />
                                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '75ms' }} />
                                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Pronunciation Feedback (Oral Mode) */}
                {mode === 'oral' && (
                    <div className="px-6 pb-2">
                        {isAnalyzingAudio && (
                            <div className="p-4 rounded-xl bg-[rgba(14,36,64,0.5)] border border-[rgba(56,189,248,0.1)] flex items-center justify-center gap-3">
                                <Spinner />
                                <span className="text-sm font-medium text-cyan-400">Analyzing nuances...</span>
                            </div>
                        )}
                        {pronunciationFeedback && !isAnalyzingAudio && (
                            <div className="p-5 rounded-2xl bg-gradient-to-r from-[rgba(14,36,64,0.6)] to-[rgba(30,58,95,0.4)] border border-[rgba(56,189,248,0.15)]">
                                <div className="flex justify-between items-start mb-4">
                                    <h3 className="text-sm font-bold text-[#f0f9ff] flex items-center gap-2 uppercase tracking-wide">
                                        <MicIcon className="w-4 h-4 text-cyan-400" /> Pronunciation Insights
                                    </h3>
                                    <span className="text-xl font-black text-gradient">{pronunciationFeedback.score}</span>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                    <div className="p-3 rounded-xl bg-[rgba(14,36,64,0.4)]">
                                        <strong className="text-cyan-400 text-xs uppercase block mb-1">Intonation</strong>
                                        <p className="text-[#94a3b8]">{pronunciationFeedback.intonation}</p>
                                    </div>
                                    <div className="p-3 rounded-xl bg-[rgba(14,36,64,0.4)]">
                                        <strong className="text-cyan-400 text-xs uppercase block mb-1">Rhythm</strong>
                                        <p className="text-[#94a3b8]">{pronunciationFeedback.rhythm}</p>
                                    </div>
                                    <div className="md:col-span-2">
                                        <div className="flex flex-wrap gap-2">
                                            {pronunciationFeedback.phonemes.map((p, i) => (
                                                <span key={i} className="px-3 py-1 rounded-lg bg-[rgba(14,36,64,0.5)] border border-[rgba(56,189,248,0.1)] text-[#94a3b8] text-xs font-mono">
                                                    {p}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="md:col-span-2">
                                        <p className="text-[#94a3b8] italic border-l-4 border-cyan-400 pl-3">
                                            "{pronunciationFeedback.suggestion}"
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Input Area */}
                <div className="p-4 md:p-6 border-t border-[rgba(56,189,248,0.1)] bg-[rgba(14,36,64,0.3)]">
                    {mode === 'writing' ? (
                        <div className="relative flex items-center gap-3">
                            <input
                                type="text"
                                value={input}
                                onChange={e => setInput(e.target.value)}
                                onKeyPress={e => e.key === 'Enter' && handleSendMessage()}
                                placeholder="Type your message..."
                                disabled={isLoading}
                                className={cn(
                                    'flex-1 px-6 py-4 rounded-2xl',
                                    'bg-[rgba(14,36,64,0.6)]',
                                    'border border-[rgba(56,189,248,0.15)]',
                                    'text-[#f0f9ff] placeholder-[#64748b]',
                                    'focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20',
                                    'transition-all duration-200'
                                )}
                            />
                            <GlassButton
                                variant="primary"
                                onClick={handleSendMessage}
                                disabled={isLoading}
                                className="h-14 w-14 !p-0 !rounded-full"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
                                    <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                                </svg>
                            </GlassButton>
                        </div>
                    ) : (
                        <div className="flex justify-center">
                            <GlassButton
                                variant={isListening ? 'danger' : 'primary'}
                                size="lg"
                                onClick={isListening ? stopOralSession : startOralSession}
                                className="relative"
                                icon={<MicIcon className="w-6 h-6" />}
                            >
                                {isListening && (
                                    <span className="absolute top-0 right-0 -mt-1 -mr-1 flex h-3 w-3">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                                        <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
                                    </span>
                                )}
                                {isListening ? 'End Conversation' : 'Start Live Conversation'}
                            </GlassButton>
                        </div>
                    )}
                </div>
            </GlassCard>
        </div>
    );
};

export default ChatTutor;
