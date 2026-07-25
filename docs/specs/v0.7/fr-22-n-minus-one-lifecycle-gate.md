# FR-22 — N-1 to N Lifecycle Regression Gate

Status: Accepted (2026-07-25)

Version: v0.7

Phase: 1

Governing decisions: ADR-002, ADR-005, ADR-010, ADR-013, ADR-014

## Problem Statement

Users rely on `dev-ready upgrade` to apply a newer overlay to a project created by an older released version without changing the upstream application or losing their work. The existing unit coverage proves pieces of that behavior inside one checkout, but it does not prove the real cross-version path. A regression could therefore ship even while all offline tests pass: generation might accidentally use checkout code, upgrade might falsify the recorded upstream pin, a dry run might mutate files, or a second upgrade might not be idempotent.

## Solution

Add a permanent network-tier lifecycle test and CI job that generates a project with the exact released N-1 artifact and then runs the checkout's lifecycle commands against it. For v0.7, the explicit baseline is `dev-ready==0.6.0`. The gate records both invocation origins, snapshots the generated project, and proves non-mutating dry-run behavior, application-byte preservation, immutable Base Provenance, advancing Overlay Currency, a clean post-upgrade check, and idempotence.

## User Stories

1. As a user upgrading a generated project, I want the upgrade path tested against a real older release, so that I can trust it outside a single source checkout.
2. As a user, I want my upstream application files to remain byte-for-byte unchanged, so that an overlay upgrade cannot silently rewrite product code.
3. As a user, I want a dry run to leave every byte unchanged, so that I can safely inspect an upgrade before applying it.
4. As a user, I want the recorded Base Provenance to remain unchanged, so that the stamp continues to describe the application content I actually received.
5. As a user, I want Overlay Currency to advance after a successful upgrade, so that lifecycle commands accurately describe the installed dev-ready overlay.
6. As a user, I want a post-upgrade check to report a clean overlay, so that a newer available base snapshot is not misreported as actionable overlay drift.
7. As a user, I want a newer base snapshot reported as an advisory, so that I can learn it exists without being told an overlay-only command installed it.
8. As a user, I want a repeated upgrade to plan no changes, so that automation and manual retries are safe.
9. As a maintainer, I want the released generator and checkout lifecycle commands to expose their origins, so that the gate cannot pass by importing the wrong code.
10. As a maintainer, I want the N-1 version to be one reviewed constant, so that CI never resolves an ambiguous or moving `latest` release.
11. As a maintainer, I want the baseline advanced only when the next development cycle begins, so that release CI always tests an artifact that actually exists.
12. As a maintainer, I want each lifecycle stage to produce a specific failure message, so that a failed gate identifies generation, check, dry-run, upgrade, preservation, or idempotence directly.
13. As a contributor, I want the ordinary unit suite to stay offline, so that the permanent network gate does not make local feedback slower or less reliable.
14. As a contributor, I want all temporary projects confined to the test-provided temporary directory, so that the gate never depends on or pollutes a developer machine.
15. As a CEO, I want this compatibility gate to merge before v0.7 feature work, so that later overlay changes build on a proven lifecycle contract.

## Implementation Decisions

- The highest test seam is a subprocess-level end-to-end scenario that treats the released artifact and checkout as two independently resolved invocation origins.
- The baseline is an explicit version constant, initially `0.6.0`; the test never asks a package index for the latest version.
- The old-generation subprocess must report its resolved package version and executable or module origin. Checkout lifecycle subprocesses must independently prove that they import the working tree.
- The scenario runs old generation, pre-upgrade check, dry run, real upgrade, post-upgrade check, and repeat upgrade in that order.
- State snapshots cover every generated file and the generation stamp. The dry-run comparison is byte-for-byte, not based only on timestamps or command output.
- Application preservation covers the backend, frontend, and all other non-overlay-managed paths. Only overlay-managed files and the stamp may change during the real upgrade.
- The stamp comparison treats its upstream repository and commit as immutable Base Provenance. The dev-ready version, selected-item pins, and managed-file inventory are Overlay Currency and may advance.
- A newer base-template pin is a non-blocking advisory because overlay-only upgrade does not materialize new upstream application bytes.
- The CI workflow owns environment setup and invokes the test; lifecycle orchestration and assertions remain in test code so they are reusable and reviewable.
- This phase is a regression gate. It does not weaken product behavior or add v0.7 feature assets to make the scenario pass.

## Testing Decisions

- The end-to-end subprocess scenario is the primary seam because it proves package isolation, CLI behavior, filesystem results, and stamp semantics together at the user boundary.
- Tests assert externally visible exit status, output evidence, file bytes, stamp fields, and the absence of a second-upgrade plan. They do not assert internal helper calls.
- The network test is explicitly marked and runs in a dedicated CI job. The offline unit suite remains unchanged in meaning.
- Failure assertions distinguish old generation, pre-check, dry run, application, preservation, post-check, and idempotence stages.
- Prior art is the existing real-generation end-to-end coverage and lifecycle unit tests; this scenario adds the missing cross-release composition rather than duplicating their internal assertions.
- The existing test, vendored-drift, and generate-and-verify jobs must remain green and retain their current responsibilities.

## Out of Scope

- Adding Handoff Protocol, Spec Loop, distribution-skill, or progress-reporting behavior.
- Updating upstream application content to a newer base-template commit.
- Looking up the latest release dynamically.
- Changing production lifecycle behavior during this gate unless a separately diagnosed FR-22 defect is approved.
- Moving network access into the unit-test tier.

## Further Notes

This is a v0.7 entry condition for the already shipped FR-22 contract, not a second upgrade feature. ADR-014 defines the Base Provenance and Overlay Currency distinction asserted here. When v0.8 development starts, the reviewed baseline should advance to `0.7.0`; it must not advance during the v0.7 release bump.
