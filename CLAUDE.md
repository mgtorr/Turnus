# CLAUDE.md - AI Assistant Guide for Turnus

**Last Updated**: 2026-01-04
**Repository**: mgtorr/Turnus
**Status**: New Project - Initial Setup

## Overview

This document serves as a comprehensive guide for AI assistants (like Claude) working on the Turnus codebase. It contains essential information about the project structure, development workflows, coding conventions, and best practices.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Development Workflows](#development-workflows)
4. [Coding Conventions](#coding-conventions)
5. [Testing Strategy](#testing-strategy)
6. [Git Workflow](#git-workflow)
7. [AI Assistant Guidelines](#ai-assistant-guidelines)
8. [Common Tasks](#common-tasks)
9. [Troubleshooting](#troubleshooting)

---

## Project Overview

### About Turnus

> **Note**: This is a new repository. Update this section with project details as development progresses.

**Project Type**: TBD
**Primary Language**: TBD
**Build System**: TBD
**Package Manager**: TBD

### Key Goals

- TBD: Document primary objectives
- TBD: Document target users/use cases
- TBD: Document key features

---

## Repository Structure

### Current Structure

```
Turnus/
├── .git/           # Git repository metadata
└── CLAUDE.md       # This file
```

### Planned Structure

> Update this section as the project develops. Typical structure might include:

```
Turnus/
├── src/            # Source code
├── tests/          # Test files
├── docs/           # Documentation
├── scripts/        # Build and utility scripts
├── config/         # Configuration files
├── .github/        # GitHub workflows and templates
├── package.json    # Dependencies (if Node.js)
├── requirements.txt # Dependencies (if Python)
├── README.md       # Project documentation
├── CLAUDE.md       # This file
└── LICENSE         # License information
```

### Key Directories

> Document each major directory's purpose as they are created:

- **`src/`**: Main source code
- **`tests/`**: Unit, integration, and end-to-end tests
- **`docs/`**: Additional documentation and guides
- **`scripts/`**: Build, deployment, and utility scripts

---

## Development Workflows

### Setting Up the Development Environment

> Update with specific setup instructions once established:

```bash
# Example setup (update as needed)
git clone <repository-url>
cd Turnus

# Install dependencies
# npm install        # for Node.js
# pip install -r requirements.txt  # for Python
# cargo build        # for Rust

# Run tests
# npm test
# pytest
# cargo test
```

### Development Cycle

1. **Branch Creation**: Create feature branch from main
2. **Development**: Make changes with frequent commits
3. **Testing**: Run tests locally before pushing
4. **Code Review**: Create PR for review
5. **Merge**: Merge to main after approval

### Build Process

> Document build commands and processes:

```bash
# Development build
# TBD

# Production build
# TBD

# Run locally
# TBD
```

---

## Coding Conventions

### General Principles

1. **Clarity over Cleverness**: Write clear, readable code
2. **DRY (Don't Repeat Yourself)**: Extract reusable components
3. **YAGNI (You Aren't Gonna Need It)**: Don't add features speculatively
4. **Single Responsibility**: Each function/class should have one clear purpose

### Style Guide

> Update with language-specific style guides:

#### Naming Conventions

- **Files**: `kebab-case.js` or `snake_case.py` (language-dependent)
- **Functions**: `camelCase()` or `snake_case()` (language-dependent)
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_prefixedWithUnderscore` or language-specific convention

#### Code Organization

- Maximum function length: ~50 lines (guideline, not strict)
- Maximum file length: ~500 lines (consider splitting larger files)
- Group related functions together
- Place helper functions near their usage

#### Comments and Documentation

- Use comments to explain **why**, not **what**
- Document public APIs and complex algorithms
- Keep comments up-to-date with code changes
- Use JSDoc/docstrings for functions and classes

Example:
```javascript
/**
 * Calculates the optimal route between two points
 * @param {Point} start - Starting location
 * @param {Point} end - Destination location
 * @param {Object} options - Routing preferences
 * @returns {Route} Optimized route object
 */
function calculateRoute(start, end, options) {
  // Implementation
}
```

### Error Handling

- Always validate input at system boundaries
- Use try-catch for operations that may fail
- Provide meaningful error messages
- Log errors appropriately for debugging

---

## Testing Strategy

### Test Organization

> Update with actual test structure:

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
└── fixtures/      # Test data and mocks
```

### Testing Guidelines

1. **Coverage**: Aim for >80% code coverage
2. **Test Naming**: Descriptive names that explain what's being tested
3. **Test Structure**: Arrange-Act-Assert pattern
4. **Isolation**: Tests should be independent and not rely on order
5. **Speed**: Keep unit tests fast (<100ms each)

### Running Tests

```bash
# Run all tests
# TBD

# Run specific test file
# TBD

# Run with coverage
# TBD

# Run in watch mode
# TBD
```

---

## Git Workflow

### Branch Naming Convention

- **Feature**: `feature/descriptive-name`
- **Bug Fix**: `fix/issue-description`
- **Hotfix**: `hotfix/critical-issue`
- **Refactor**: `refactor/component-name`
- **Claude AI**: `claude/claude-md-*` (auto-generated)

### Commit Message Format

Follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(auth): add OAuth2 authentication

Implement OAuth2 authentication flow with Google and GitHub providers.
Includes token refresh logic and session management.

Closes #123
```

```
fix(api): handle null response in user endpoint

Added null check to prevent crashes when user data is unavailable.
```

### Pull Request Process

1. Create PR with descriptive title and description
2. Link related issues
3. Ensure all tests pass
4. Request review from team members
5. Address review comments
6. Squash and merge once approved

---

## AI Assistant Guidelines

### Core Principles for AI Assistants

When working on this codebase, AI assistants should:

1. **Read Before Writing**: Always read existing code before making changes
2. **Maintain Consistency**: Follow existing patterns and conventions
3. **Minimize Changes**: Only modify what's necessary for the task
4. **Test Thoroughly**: Run tests after changes
5. **Document Changes**: Update relevant documentation
6. **Ask When Unclear**: Request clarification rather than making assumptions

### Preferred Workflow

1. **Understand the Request**: Clarify requirements if ambiguous
2. **Explore the Codebase**: Use grep/glob to find relevant files
3. **Read Existing Code**: Understand current implementation
4. **Plan Changes**: Consider impact and approach
5. **Implement**: Make focused, incremental changes
6. **Test**: Verify changes work as expected
7. **Document**: Update comments and docs as needed
8. **Commit**: Create clear commit message

### Code Modification Best Practices

✅ **DO**:
- Read files before editing them
- Follow existing code style and patterns
- Add tests for new functionality
- Update documentation when changing behavior
- Use meaningful variable and function names
- Handle errors appropriately
- Keep changes focused and atomic

❌ **DON'T**:
- Make changes without reading existing code
- Introduce new patterns without discussion
- Add unnecessary abstractions
- Create files when editing existing ones would work
- Add features beyond what was requested
- Skip testing critical functionality
- Leave commented-out code

### Security Considerations

Always check for:
- **Input Validation**: Sanitize user inputs
- **SQL Injection**: Use parameterized queries
- **XSS**: Escape user-generated content
- **Authentication**: Verify user permissions
- **Secrets**: Never commit credentials or API keys
- **Dependencies**: Keep dependencies updated

### Performance Considerations

- Avoid N+1 queries
- Use appropriate data structures
- Cache expensive computations
- Optimize hot paths
- Profile before optimizing
- Consider memory usage for large datasets

---

## Common Tasks

### Adding a New Feature

1. Create feature branch: `git checkout -b feature/feature-name`
2. Explore existing code to understand where feature fits
3. Implement feature following existing patterns
4. Add tests for new functionality
5. Update documentation
6. Commit and push
7. Create pull request

### Fixing a Bug

1. Create fix branch: `git checkout -b fix/bug-description`
2. Reproduce the bug (write failing test if possible)
3. Identify root cause
4. Implement fix
5. Verify fix with tests
6. Commit and push
7. Create pull request

### Refactoring Code

1. Ensure tests exist for code being refactored
2. Create refactor branch: `git checkout -b refactor/component-name`
3. Make incremental changes
4. Run tests after each change
5. Commit frequently
6. Update documentation if interfaces changed
7. Create pull request

### Updating Dependencies

> Add specific dependency update procedures:

```bash
# Check for outdated dependencies
# TBD

# Update dependencies
# TBD

# Test after updates
# TBD
```

---

## Troubleshooting

### Common Issues

> Document common issues and solutions as they arise:

#### Issue: [Problem Description]
**Solution**: [How to fix]

#### Issue: Tests Failing After Changes
**Solution**:
1. Check test output for specific failures
2. Verify dependencies are installed
3. Clear cache/build artifacts
4. Run tests in isolation

#### Issue: Build Failures
**Solution**:
1. Check build logs for errors
2. Verify all dependencies are installed
3. Check for syntax errors
4. Ensure configuration files are correct

### Getting Help

- **Documentation**: Check docs/ directory
- **Issues**: Search existing GitHub issues
- **Team**: Contact project maintainers
- **Logs**: Check application logs for errors

---

## Maintenance

### Updating This Document

This CLAUDE.md file should be updated when:

- Project structure changes significantly
- New development practices are adopted
- New tools or dependencies are added
- Common patterns or conventions evolve
- New common issues are discovered

**Update Process**:
1. Make changes to CLAUDE.md
2. Commit with message: `docs: update CLAUDE.md with [description]`
3. Include in relevant pull request or create dedicated PR

### Document Sections to Update

As the project develops, prioritize updating:

1. ✅ **Project Overview**: When project goals are defined
2. ✅ **Repository Structure**: As directories are created
3. ✅ **Development Workflows**: When build process is established
4. ✅ **Coding Conventions**: Based on team decisions
5. ✅ **Testing Strategy**: When test framework is chosen
6. ✅ **Common Tasks**: As patterns emerge

---

## Appendix

### Useful Commands Reference

```bash
# Git commands
git status                          # Check working tree status
git log --oneline --graph -10       # View recent commits
git branch -a                       # List all branches
git diff                           # View changes

# Common development commands (update as needed)
# TBD
```

### External Resources

> Add links to relevant documentation:

- Project Documentation: TBD
- API Documentation: TBD
- Design Documents: TBD
- Team Wiki: TBD

---

## Version History

| Version | Date       | Changes                          | Author |
|---------|------------|----------------------------------|--------|
| 1.0.0   | 2026-01-04 | Initial CLAUDE.md creation       | Claude |

---

**Note**: This is a living document. Keep it updated as the project evolves to ensure AI assistants and developers have accurate, current information about the codebase.
