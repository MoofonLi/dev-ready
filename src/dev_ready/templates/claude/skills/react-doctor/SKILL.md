---
name: react-doctor
description: Diagnose and health-check the React frontend codebase using react-doctor. Use when reviewing frontend code, fixing React performance issues, or verifying component best practices.
---

# React doctor skill

Use `react-doctor` to analyze the React frontend application for common performance bottlenecks, anti-patterns, and component health issues.

## When to run

- Before finalizing major React component changes or refactors.
- When investigating frontend performance regressions, unexpected re-renders, or memory leaks.
- As part of periodic frontend code quality reviews.

## How to run

From the `frontend/` directory:

```bash
cd frontend && npm run doctor
```

## Interpreting results and acting on findings

1. **Re-render warnings**: Check component memoization (`useMemo`, `useCallback`) and object/array reference stability in props.
2. **Hook usage rules**: Verify hook dependency arrays and ensure hooks are called unconditionally at the top level.
3. **State management**: Avoid redundant state that can be derived during rendering.
4. **Action**: Apply targeted code fixes to address reported issues, re-run `npm run doctor`, and confirm warnings are resolved.
