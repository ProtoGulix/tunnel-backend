# GitHub Copilot Instructions

## Core Principles (Reusable)

### 1. YAGNI - You Aren't Gonna Need It

Code only what's explicitly asked. No "improvements" or "future-proofing" without request.

### 2. KISS - Keep It Simple, Stupid

One solution, tested, delivered. No multiple variations (never 3 run scripts for one purpose).

### 3. Transparency

Explain decision before acting: "I'll modify X because Y". Ask if scope is ambiguous.

### 4. Testability

Never create code that can't be tested immediately. No "should work" - verify now.

### 5. Human Code

Write code a human understands in 30 seconds. No over-engineering, no enterprise patterns.

### 6. Agnostic Outputs Only

Keep wording and manifests provider-agnostic. Treat the repo as the sole source of truth.

### 7. README Maintenance

Update README.md when implementing features or significant changes. Keep it agnostic: no business details, no technical implementation. Focus on project purpose and general capabilities only.

---

## What NOT To Do (Reusable)

| ❌ Never                                  | ✅ Do Instead             |
| ----------------------------------------- | ------------------------- |
| Create run-dev.ps1, run-dev.bat, Makefile | One script only           |
| Add complex logging_config.py             | Use logging.basicConfig() |
| Create docs without being asked           | Write clear code comments |
| Test scripts that don't run               | Don't create if untested  |
| 7+ files for 1 feature                    | Max 2 files per feature   |

---

## Your Role in One Sentence (Reusable)

Build simple, tested, working code that does exactly what was asked - nothing more.
