# FluentFlow AI - Project Context

## Project Overview
FluentFlow AI is an advanced language learning platform designed to provide deep pedagogical value through AI-driven personalization. It goes beyond simple vocabulary retention to ensure genuine student follow-up and mastery of linguistic concepts.

## Core Pedagogical Philosophy
- **Student Follow-up**: The system must track not just what words are known, but the depth of understanding (nuance, context, usage).
- **Deep Knowledge**: Focus on grammatical structure, cultural context, and conversational fluidity.
- **Pedagogical AI**: The AI acts as a tutor, identifying weak points and adapting the curriculum dynamically.

## Feature Requirements
- **Multi-Language Support**: Must include major global languages AND Scandinavian languages (Norwegian, Swedish, Danish).
- **Alert & Export System**:
    - automated alerts for study schedules.
    - Ability to export study sessions/deadlines to external calendars (Outlook, Google Calendar, etc.).
- **Progress Tracking**: Detailed mastery analytics.

## Technology Stack
- **Frontend**: React (Vite)
- **Backend/Database**: Supabase (Auth, Database, Realtime)
- **Hosting/Deployment**: Vercel
- **Version Control**: GitHub
- **AI Integration**: Google GenAI / Anthropic (as configured)

## Infrastructure Guides
### Supabase Setup (Manual Required)
1. Create a new Project in Supabase.
2. Enable Auth (Email/Password).
3. Create Database tables for `users`, `progress`, `vocab`.

### Deployment (Manual Required)
1. Push code to a GitHub repository.
2. Import repository into Vercel.
3. Configure Environment Variables in Vercel.
