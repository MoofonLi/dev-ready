# ADR-002: Manifest-pinned upstream with CI-gated bumps

- Status: Accepted
- Context: A "fetch latest at generation time" design was evaluated and rejected — it ships untested template/overlay combinations and transfers maintenance burden to users.
- Decision: `manifest.json` pins the exact upstream commit, acting as a lockfile. A weekly GitHub Actions workflow opens a PR bumping the pin; CI regenerates a project and verifies it before merge.
- Consequences: Every released version generates a tested combination. Maintenance is a scheduled, automated review task rather than user-facing breakage. The manifest ships inside the package (`src/dev_ready/manifest.json`) so an installed CLI always carries the pin it was released with.
