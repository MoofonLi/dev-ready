# ADR-001: Two-stage generation, no upstream fork

- Status: Accepted
- Context: We layer AI tooling on top of fastapi/full-stack-fastapi-template. Forking it creates a permanent merge liability against a fast-moving upstream.
- Decision: Never fork. Fetch upstream as a snapshot at a pinned commit, then apply our overlay files on top.
- Consequences: Upstream stays independent; our value-add is isolated in the overlay; upstream changes are absorbed via a controlled bump process (ADR-002).
