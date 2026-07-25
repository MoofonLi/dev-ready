# FR-29 — Staged Init Progress Reporting

Status: Accepted (2026-07-25)

Version: v0.7

Phase: 4

Governing decisions: ADR-002, ADR-003, ADR-004, ADR-013

## Problem Statement

Project generation can spend meaningful time fetching, applying the overlay, verifying output, and finalizing the target while the user sees no structured progress. Lower-level warning output currently crosses the terminal-policy boundary, and finalization can use move behavior that falls back to cross-filesystem copying, creating a partial-visibility window. Users need honest progress without breaking stdout automation, and a reported failure must never expose a partial target.

## Solution

Expose typed observational progress events for exactly four generation stages: fetch, overlay, verify, and finalize. The CLI renders those events on stderr as a spinner for TTY users or stable plain lines for redirected output, while stdout retains the existing final report. Generation stages remain terminal-agnostic. Finalization stages beside the destination and commits with one same-filesystem atomic directory rename after revalidating the target.

## User Stories

1. As a user running init interactively, I want visible activity during each real generation stage, so that I know the command is progressing.
2. As a user redirecting output, I want stable plain progress lines, so that logs remain readable and machine-safe.
3. As a user consuming stdout, I want progress confined to stderr, so that the existing final report contract remains usable.
4. As a user, I want exactly four named stages in pipeline order, so that progress corresponds to meaningful work rather than arbitrary percentages.
5. As a user, I want the fetch line to show the manifest-pinned commit, so that I can see which reproducible base is being retrieved.
6. As a user, I want completed and failed stages to include elapsed time, so that slow or failing operations are diagnosable.
7. As a user, I want a failed stage identified once and unambiguously, so that the subsequent error and exit code have clear context.
8. As a user in CI, I want no animation control characters, so that redirected logs are deterministic and clean.
9. As a user, I want no speculative percentages, so that the display never claims precision the pipeline cannot measure.
10. As a user interrupting generation, I want the active spinner stopped, so that my terminal is restored cleanly.
11. As a user encountering an unexpected exception, I want the active progress renderer closed, so that terminal cleanup is reliable even outside typed failures.
12. As a programmatic caller, I want progress callbacks to be optional, so that existing integrations retain their behavior.
13. As a programmatic caller, I want stage identity represented as typed data, so that I do not need to parse human display text.
14. As a programmatic caller, I want a faulty observer isolated from generation, so that reporting cannot make an otherwise valid generation fail.
15. As a user, I want temporary-cleanup warnings rendered through the CLI, so that lower modules never unexpectedly print to my terminal.
16. As a user, I want cleanup warnings treated separately from pipeline stages, so that the four-stage contract remains truthful.
17. As a user generating into a new target, I want no partial target visible if any stage fails, so that failure remains all-or-nothing.
18. As a user generating into an initially empty target directory, I want that empty state restored after failure, so that initialization does not leave a changed destination.
19. As a user, I want finalization to re-check the destination immediately before commit, so that a concurrent target conflict cannot be overwritten.
20. As a maintainer, I want no new runtime dependency for progress, so that installation and startup remain lightweight.
21. As a maintainer, I want terminal behavior owned by the CLI, so that fetch, overlay, verification, and generation logic remain reusable.
22. As a maintainer, I want deterministic clock, stream, and TTY seams, so that progress tests do not sleep or depend on a real terminal.
23. As a maintainer, I want stage-specific exit codes preserved, so that fetch, overlay, verification, and finalization failures remain compatible with the CLI contract.
24. As a future internationalization maintainer, I want the final progress string set established first, so that v0.8 can translate one stable interface.

## Implementation Decisions

- Generation accepts an optional progress observer and emits typed start, completion, and failure events for fetch, overlay, verify, and finalize in that order.
- Stage identity and status are typed values, not display strings. The fetch-start event includes the manifest-pinned commit; terminal events carry elapsed time.
- Progress is observational. The event sink is isolated so that an observer exception cannot escape into generation or alter the result.
- The CLI exclusively owns stream selection, TTY detection, spinner lifecycle, display strings, elapsed-time formatting, and rendering of non-stage warnings.
- Progress is written to stderr. Existing normal output and the final generation report remain on stdout.
- TTY stderr uses a standard-library-only spinner while a stage is active. Non-TTY stderr uses stable plain start and terminal lines with no ANSI or other control characters.
- The renderer has an idempotent close path invoked from a finalization guard. It stops active animation after success, typed errors, unexpected exceptions, keyboard interruption, and termination signals handled by Python.
- Temporary cleanup failures produce a CLI-rendered warning event. They do not create a fifth progress stage.
- Fetch, overlay, and verification interfaces remain unaware of terminal rendering and TTY state.
- Finalization creates staging adjacent to the target on the same filesystem, revalidates destination availability, and commits the complete directory with one atomic rename.
- Cross-filesystem move fallback is not used for the final commit. Any finalize failure removes staging and leaves no partial target.
- If generation temporarily removes an existing empty target to enable the atomic commit, failure restores that empty target state.
- The established failure mapping remains: fetch exits 3, overlay exits 1, verification exits 5, and finalization exits 4.
- No runtime dependency is added. Clock, stderr stream, TTY determination, and animation timing are injectable at test seams.

## Testing Decisions

- Two high seams are necessary: the generation callback proves typed pipeline events independent of presentation, and the CLI entry point proves terminal rendering, cleanup, stdout/stderr separation, and exit mapping.
- Generator tests assert exactly one start and one terminal event per entered stage, strict stage order, pinned-commit data, elapsed values, and unchanged behavior when no callback is supplied.
- Observer-failure tests prove that a raising callback does not change generation success or the underlying failure being reported.
- CLI tests use fake clocks, streams, and TTY responses. They do not sleep or require a real terminal.
- Non-TTY tests assert stable lines and the absence of ANSI and control characters. TTY tests assert active animation is stopped and a terminal status is rendered.
- Failure injection covers fetch, overlay, verify, and finalize, preserving exit codes and producing one failed-stage line.
- Cleanup coverage includes typed exceptions, unexpected exceptions, keyboard interruption, supported termination handling, and temporary-cleanup warnings.
- Filesystem tests observe the target boundary: every pre-finalize failure leaves it untouched, finalize failure exposes no partial directory, and an initially empty target is restored.
- A destination race is simulated between staging and commit to prove revalidation refuses overwrite.
- Existing generation, CLI, report, and real-generation tests provide prior art. Assertions are updated only where stderr now has a documented contract.

## Out of Scope

- Percent-complete estimates or byte-level fetch progress.
- More than four pipeline stages.
- Progress on stdout or changing the final report format.
- New runtime dependencies or a third-party spinner library.
- Terminal rendering inside fetch, overlay, verification, or other lower modules.
- FR-25 translation catalogs or localized progress strings.
- Changing existing CLI flags or failure exit codes.

## Further Notes

The CLI specification must document stderr behavior and the four-stage vocabulary. FR-29 intentionally precedes internationalization so v0.8 can translate the settled user-visible strings. Same-filesystem staging is part of the feature's truthfulness: a command cannot report finalize failure after exposing a partially copied target.
