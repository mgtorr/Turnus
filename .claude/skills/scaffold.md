---
name: scaffold
description: Use this to generate professional project structures, boilerplate, and standardized configurations for new features or repositories.
---

# Scaffold Skill
When the user asks to "scaffold," "initialize," or "setup" a project or feature, you must enforce high-level architectural standards.

## Instructions
1. **Identify the Stack:** Determine the language, framework, and environment.
2. **Define the Skeleton:** Create a directory structure that follows industry best practices (e.g., separating `src`, `tests`, `docs`, and `config`).
3. **Generate Boilerplate:** - Create a `README.md` with clear setup instructions.
   - Include a `.gitignore` relevant to the stack.
   - Add a `CLAUDE.md` for project-specific rules.
4. **Configuration:** Generate base config files (e.g., `tsconfig.json`, `ruff.toml`, `jest.config.js`).

## Requirements
- Never provide a single-file solution for a multi-file problem.
- Always include a test directory by default.
- Every scaffold must include a "Rationale" section explaining why this structure was chosen.
