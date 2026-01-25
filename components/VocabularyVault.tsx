import React, { useState } from 'react';
import { VocabularyItem } from '../types';
import GlassCard from './ui/GlassCard';
import GlassButton from './ui/GlassButton';
import GlassInput from './ui/GlassInput';
import GlassProgress from './ui/GlassProgress';


interface VocabularyVaultProps {
    vocabulary: VocabularyItem[];
    onAddWord: (word: string) => void;
}

const VocabularyVault: React.FC<VocabularyVaultProps> = ({ vocabulary, onAddWord }) => {
    const [newWord, setNewWord] = useState('');
    const [isAdding, setIsAdding] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    const handleAdd = async () => {
        if (newWord.trim()) {
            setIsAdding(true);
            await onAddWord(newWord.trim());
            setNewWord('');
            setIsAdding(false);
        }
    };

    const filteredVocabulary = vocabulary.filter(item =>
        item.word.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.translation.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                <div>
                    <h1 className="text-4xl font-black text-[#f0f9ff] tracking-tight">
                        Vocabulary <span className="text-gradient">Vault</span>
                    </h1>
                    <p className="text-[#94a3b8] mt-2">
                        Your personal collection of words and phrases.
                    </p>
                </div>

                {/* Add Word Section */}
                <div className="flex gap-3 w-full lg:w-auto">
                    <GlassInput
                        type="text"
                        value={newWord}
                        onChange={(e) => setNewWord(e.target.value)}
                        placeholder="Add a new word..."
                        onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
                        className="flex-1 lg:w-64"
                        icon={
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                            </svg>
                        }
                    />
                    <GlassButton
                        variant="primary"
                        onClick={handleAdd}
                        disabled={isAdding || !newWord.trim()}
                        loading={isAdding}
                    >
                        {isAdding ? 'Adding...' : 'Add'}
                    </GlassButton>
                </div>
            </header>

            {/* Search */}
            {vocabulary.length > 0 && (
                <GlassInput
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search your vocabulary..."
                    icon={
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                        </svg>
                    }
                    className="max-w-md"
                />
            )}

            {/* Vocabulary Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredVocabulary.map((item) => (
                    <GlassCard
                        key={item.id}
                        padding="md"
                        className="group"
                    >
                        {/* Header */}
                        <div className="flex justify-between items-start mb-4">
                            <h3 className="text-xl font-bold text-[#f0f9ff] group-hover:text-cyan-400 transition-colors">
                                {item.word}
                            </h3>
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-cyan-400">
                                    {item.masteryLevel}%
                                </span>
                            </div>
                        </div>

                        {/* Mastery Progress */}
                        <GlassProgress
                            value={item.masteryLevel}
                            variant="cyan"
                            size="sm"
                            className="mb-4"
                        />

                        {/* Translation */}
                        <p className="text-teal-400 font-medium mb-3">
                            {item.translation}
                        </p>

                        {/* Definition */}
                        <p className="text-[#94a3b8] text-sm mb-4 italic">
                            "{item.definition}"
                        </p>

                        {/* Example */}
                        <div className="p-4 rounded-xl bg-[rgba(14,36,64,0.4)] border border-[rgba(56,189,248,0.1)]">
                            <p className="text-[#64748b] text-xs font-bold uppercase tracking-wider mb-2">
                                Example
                            </p>
                            <p className="text-[#94a3b8] text-sm">
                                {item.exampleSentence}
                            </p>
                        </div>
                    </GlassCard>
                ))}

                {/* Empty State */}
                {filteredVocabulary.length === 0 && vocabulary.length === 0 && (
                    <div className="col-span-full">
                        <GlassCard className="text-center py-16" hover={false}>
                            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-[rgba(6,182,212,0.1)] flex items-center justify-center">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-cyan-400" viewBox="0 0 20 20" fill="currentColor">
                                    <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-bold text-[#f0f9ff] mb-2">
                                No words saved yet
                            </h3>
                            <p className="text-[#94a3b8] max-w-md mx-auto">
                                Start building your vocabulary by adding words above. Each word you learn earns you XP!
                            </p>
                        </GlassCard>
                    </div>
                )}

                {/* No Search Results */}
                {filteredVocabulary.length === 0 && vocabulary.length > 0 && (
                    <div className="col-span-full">
                        <GlassCard className="text-center py-12" hover={false}>
                            <p className="text-[#94a3b8]">
                                No words match your search. Try a different term.
                            </p>
                        </GlassCard>
                    </div>
                )}
            </div>

            {/* Stats Footer */}
            {vocabulary.length > 0 && (
                <div className="flex items-center justify-center gap-8 pt-6 border-t border-[rgba(56,189,248,0.1)]">
                    <div className="text-center">
                        <p className="text-3xl font-black text-gradient">{vocabulary.length}</p>
                        <p className="text-xs text-[#64748b] uppercase tracking-wider">Total Words</p>
                    </div>
                    <div className="text-center">
                        <p className="text-3xl font-black text-teal-400">
                            {vocabulary.filter(v => v.masteryLevel >= 80).length}
                        </p>
                        <p className="text-xs text-[#64748b] uppercase tracking-wider">Mastered</p>
                    </div>
                    <div className="text-center">
                        <p className="text-3xl font-black text-amber-400">
                            {vocabulary.filter(v => v.masteryLevel < 50).length}
                        </p>
                        <p className="text-xs text-[#64748b] uppercase tracking-wider">Learning</p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default VocabularyVault;
