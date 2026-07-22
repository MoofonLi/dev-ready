#!/usr/bin/env python3
"""Bump commit sha pins for all vendored external repositories in manifest.json.

Phase 1 stub script: no vendored repos are configured yet.
Phase 2 will implement full bump logic.
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    print("no vendored repos to bump")
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write("changed=false\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
