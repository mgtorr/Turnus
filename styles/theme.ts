// FluentFlow AI - Ocean Blues Theme
// Glassmorphism 2.0 with noise textures, layered transparency, frosted glass

export const colors = {
    // Background colors - Deep ocean palette
    bg: {
        primary: '#030712',      // Near black, deep ocean
        secondary: '#0a1628',    // Deep navy
        tertiary: '#1e3a5f',     // Navy blue
    },

    // Glass effect colors
    glass: {
        bg: 'rgba(14, 36, 64, 0.6)',
        bgLight: 'rgba(14, 36, 64, 0.4)',
        bgDark: 'rgba(14, 36, 64, 0.7)',
        border: 'rgba(56, 189, 248, 0.15)',
        borderHover: 'rgba(6, 182, 212, 0.4)',
        highlight: 'rgba(255, 255, 255, 0.05)',
    },

    // Accent colors
    accent: {
        primary: '#06b6d4',      // Cyan
        secondary: '#14b8a6',    // Teal
        warm: '#f59e0b',         // Gold
        glow: 'rgba(6, 182, 212, 0.4)',
    },

    // Text colors
    text: {
        primary: '#f0f9ff',      // Ice white
        secondary: '#94a3b8',    // Slate
        muted: '#64748b',        // Muted slate
    },

    // Status colors
    status: {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#06b6d4',
    },
} as const;

// CSS custom properties for easy access
export const cssVariables = `
    :root {
        /* Background */
        --bg-primary: ${colors.bg.primary};
        --bg-secondary: ${colors.bg.secondary};
        --bg-tertiary: ${colors.bg.tertiary};

        /* Glass */
        --glass-bg: ${colors.glass.bg};
        --glass-bg-light: ${colors.glass.bgLight};
        --glass-bg-dark: ${colors.glass.bgDark};
        --glass-border: ${colors.glass.border};
        --glass-border-hover: ${colors.glass.borderHover};
        --glass-highlight: ${colors.glass.highlight};

        /* Accents */
        --accent-primary: ${colors.accent.primary};
        --accent-secondary: ${colors.accent.secondary};
        --accent-warm: ${colors.accent.warm};
        --accent-glow: ${colors.accent.glow};

        /* Text */
        --text-primary: ${colors.text.primary};
        --text-secondary: ${colors.text.secondary};
        --text-muted: ${colors.text.muted};

        /* Status */
        --success: ${colors.status.success};
        --error: ${colors.status.error};
        --warning: ${colors.status.warning};
        --info: ${colors.status.info};
    }
`;

// Skill colors updated for ocean theme
export const SKILL_COLORS_GLASS = {
    'Writing': 'bg-cyan-500/80 border-cyan-400/50 text-cyan-300',
    'Oral': 'bg-emerald-500/80 border-emerald-400/50 text-emerald-300',
    'Test': 'bg-amber-500/80 border-amber-400/50 text-amber-300',
    'General Study': 'bg-violet-500/80 border-violet-400/50 text-violet-300',
} as const;

// Gradient presets
export const gradients = {
    primary: 'bg-gradient-to-r from-cyan-500 to-teal-500',
    secondary: 'bg-gradient-to-r from-violet-500 to-purple-500',
    accent: 'bg-gradient-to-r from-amber-400 to-orange-500',
    glass: 'bg-gradient-to-br from-[rgba(14,36,64,0.7)] to-[rgba(14,36,64,0.4)]',
    text: 'bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent',
} as const;
