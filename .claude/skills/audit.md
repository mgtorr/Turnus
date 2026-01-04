---
name: audit
description: Use this for a ruthless, objective review of code, logic, or strategy to find blind spots, inefficiencies, and risks.
---

# Audit Skill

When the user asks for an "audit," "review," or "critique," do not be polite. Be precise and surgical.

## Instructions

1. **Identify Vulnerabilities:** Look for security flaws (hardcoded keys, injection risks).
2. **Dissect Logic:** Point out redundant operations, O(n^2) complexities where O(n) is possible, and edge cases that will break the system.
3. **Assess Strategy:** If it's a non-code document, find the logical leaps and unverified assumptions.
4. **Categorize Findings:**
   - **Critical:** Fix immediately or the system fails/is breached.
   - **Technical Debt:** Will slow down future development.
   - **Nitpick:** Stylistic or minor optimizations.

## Rules

- [Inference] You must assume the user has missed at least one critical edge case.
- Do not validate the user's effort; only evaluate the output.
