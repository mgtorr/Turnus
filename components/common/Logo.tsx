import React from 'react';

interface LogoProps {
    className?: string;
}

const Logo: React.FC<LogoProps> = ({ className = "w-10 h-10" }) => {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" className={className} fill="none">
            <defs>
                <linearGradient id="logoGradient" x1="10" y1="10" x2="90" y2="90" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#06b6d4" /> {/* cyan-500 */}
                    <stop offset="1" stopColor="#14b8a6" /> {/* teal-500 */}
                </linearGradient>
            </defs>

            {/* Background Shape - Abstract Chat Bubble */}
            <path
                d="M20 50C20 33.4315 33.4315 20 50 20C66.5685 20 80 33.4315 80 50C80 60 75 69 67 74L65 85L55 80C53.3 80.2 51.7 80.2 50 80.2C33.4 80.2 20 66.8 20 50Z"
                fill="url(#logoGradient)"
                fillOpacity="0.15"
            />

            {/* Flow Wave Lines */}
            <path
                d="M35 50C35 50 42 42 50 42C58 42 65 50 65 50"
                stroke="url(#logoGradient)"
                strokeWidth="6"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
            <path
                d="M35 50C35 50 42 58 50 58C58 58 65 50 65 50"
                stroke="url(#logoGradient)"
                strokeWidth="6"
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity="0.7"
            />

            {/* Dot for emphasis */}
            <circle cx="72" cy="28" r="4" fill="#06b6d4" />
        </svg>
    );
};

export default Logo;