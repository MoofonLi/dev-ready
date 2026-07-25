# Ticket files

The `senior_engineer` role creates one Markdown file per tracer-bullet ticket in this directory after reading `../../protocol.yaml` and the accepted durable spec.

Each ticket records:

- what end-to-end behavior it delivers;
- blocking ticket ids;
- its exact file footprint;
- `parallel-safe: yes` or `parallel-safe: no`;
- testable acceptance criteria.

Execution takes one unblocked ticket at a time. Parallel work is allowed only where the ticket and Protocol Configuration permit it.
