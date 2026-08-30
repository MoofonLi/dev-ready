#!/usr/bin/env python3
"""Check dev-ready-authored upstream claims against the generated tree."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Literal, NamedTuple


# This is a claim-to-source mapping, not a second copy of AGENTS.md.  Claims
# are matched case-insensitively in the authored claim file; source needles are
# the upstream representation of the same fact and may use the project's names.
class SourceFact(NamedTuple):
    """The upstream path and evidence for one authored claim."""

    path: str
    needles: tuple[str, ...]
    kind: Literal["file", "directory"] = "file"


class ClaimFact(NamedTuple):
    """One authored claim and the upstream evidence that keeps it true."""

    label: str
    claim_path: str
    claim_needles: tuple[str, ...]
    sources: tuple[SourceFact, ...]
    forbidden_sources: tuple[SourceFact, ...] = ()
    claim_root: Literal["project", "repository"] = "project"


def _file(path: str, *needles: str) -> SourceFact:
    return SourceFact(path, needles)


def _directory(path: str) -> SourceFact:
    return SourceFact(path, (), "directory")


STACK_FACTS: dict[str, SourceFact] = {
    "FastAPI": _file("backend/pyproject.toml", "fastapi"),
    "SQLModel": _file("backend/pyproject.toml", "sqlmodel"),
    "PostgreSQL": _file("backend/pyproject.toml", "psycopg"),
    "Pydantic": _file("backend/pyproject.toml", "pydantic"),
    "Alembic": _file("backend/pyproject.toml", "alembic"),
    "React": _file("frontend/package.json", '"react":'),
    "TypeScript": _file("frontend/package.json", '"typescript":'),
    "Vite": _file("frontend/package.json", '"vite":'),
    "Tailwind CSS": _file("frontend/package.json", '"tailwindcss":'),
    "shadcn/ui": _file("frontend/components.json", "ui.shadcn.com"),
    "TanStack Query": _file("frontend/package.json", "@tanstack/react-query"),
    "TanStack Router": _file("frontend/package.json", "@tanstack/react-router"),
    "TanStack Table": _file("frontend/package.json", "@tanstack/react-table"),
    "react-hook-form": _file("frontend/package.json", "react-hook-form"),
    "zod": _file("frontend/package.json", "zod"),
    "database": _file("compose.yml", "db:"),
    "Docker Compose": _file("compose.yml", "services:"),
    "Traefik": _file("compose.yml", "traefik"),
    "live services": _file("compose.yml", "services:"),
    "docker compose watch": _file("compose.override.yml", "watch:"),
    "db mailcatcher": _file("compose.override.yml", "db:", "mailcatcher:"),
    "scripts/prestart.sh": _file("backend/scripts/prestart.sh", "alembic upgrade head"),
    "scripts/tests-start.sh": _file("backend/scripts/tests-start.sh", "bash scripts/test.sh"),
    "scripts/lint.sh": _file(
        "backend/scripts/lint.sh",
        "mypy app",
        "ty check app",
        "ruff check app",
        "ruff format app --check",
    ),
    "scripts/format.sh": _file("backend/scripts/format.sh", "ruff format"),
    "pytest": _file("backend/pyproject.toml", "pytest"),
    "coverage": _file("backend/pyproject.toml", "coverage"),
    "ruff check": _file("backend/scripts/lint.sh", "ruff check"),
    "ruff format": _file("backend/scripts/lint.sh", "ruff format"),
    "mypy": _file("backend/pyproject.toml", "mypy", "strict = true"),
    "ty": _file("backend/pyproject.toml", "ty"),
    "Bun": _file("bun.lock"),
    "Playwright": _file("frontend/package.json", '"test": "bunx playwright test'),
    "biome": _file("frontend/package.json", '"lint": "biome check'),
    "tsc": _file("frontend/package.json", '"build": "tsc -p tsconfig.build.json'),
    "90%": _file(".github/workflows/test-backend.yml", "--fail-under=90"),
    "generated frontend API client": _directory("frontend/src/client"),
    "client-generation script": _file("frontend/package.json", "generate-client"),
    "generated route tree": _file("frontend/src/routeTree.gen.ts"),
    "Alembic migration": _directory("backend/app/alembic"),
    "backend tests mirror": _directory("backend/tests"),
    "FastAPI application": _file("backend/app/main.py", "from fastapi import fastapi"),
    "React application": _file("frontend/package.json", '"react":'),
    "SQLModel models": _file("backend/app/models.py", "sqlmodel"),
    "Alembic migrations": _directory("backend/app/alembic"),
    "Backend": _directory("backend"),
    "Frontend": _directory("frontend"),
    "Infra": _file("compose.yml", "services:"),
    "backend/": _directory("backend"),
    "frontend/": _directory("frontend"),
    "app/main.py": _file("backend/app/main.py"),
    "compose.yml": _file("compose.yml"),
    "compose.override.yml": _file("compose.override.yml"),
    "fastapi dev app/main.py": _file("backend/app/main.py", "app = fastapi("),
    "bun install": _file("package.json", '"workspaces"'),
    "bun run dev": _file("frontend/package.json", '"dev": "vite"'),
    "fastapi/full-stack-fastapi-template": _file(
        "README.md", "fastapi/full-stack-fastapi-template"
    ),
    "tsconfig.build.json": _file("frontend/tsconfig.build.json"),
    "pytest with coverage": _file("backend/scripts/test.sh", "coverage run -m pytest"),
    "biome check ./": _file("frontend/package.json", '"@biomejs/biome"'),
    "biome format --write ./": _file("frontend/package.json", '"@biomejs/biome"'),
}


_SETUP_PROJECT_SKILL = ".agents/skills/setup-project/SKILL.md"
_SETUP_PROJECT_EMAIL = (
    ".agents/skills/setup-project/email-and-error-reporting.md"
)
SETUP_PROJECT_FACTS = (
    ClaimFact(
        "setup-project superuser lifecycle",
        _SETUP_PROJECT_SKILL,
        (
            "creates the superuser on first start",
            "looks it up by email",
            "startup initializer runs on every start",
        ),
        (
            _file("backend/scripts/prestart.sh", "python app/initial_data.py"),
            _file(
                "backend/app/core/db.py",
                "select(User).where(User.email == settings.FIRST_SUPERUSER)",
                "if not user:",
                "password=settings.FIRST_SUPERUSER_PASSWORD",
                "is_superuser=True",
            ),
            _file(
                "compose.yml",
                "command: bash scripts/prestart.sh",
                "condition: service_completed_successfully",
            ),
        ),
    ),
    ClaimFact(
        "setup-project required superuser settings",
        _SETUP_PROJECT_SKILL,
        ("required settings and cannot simply be deleted",),
        (
            _file(
                "backend/app/core/config.py",
                "FIRST_SUPERUSER: EmailStr",
                "FIRST_SUPERUSER_PASSWORD: str",
            ),
            _file(
                "compose.yml",
                "FIRST_SUPERUSER: ${FIRST_SUPERUSER?Variable not set}",
                "FIRST_SUPERUSER_PASSWORD: ${FIRST_SUPERUSER_PASSWORD?Variable not set}",
            ),
        ),
    ),
    ClaimFact(
        "setup-project SMTP defaults",
        _SETUP_PROJECT_EMAIL,
        ("SMTP_PORT=587", "SMTP_TLS=True", "SMTP_SSL=False"),
        (
            _file(".env", "SMTP_PORT=587", "SMTP_TLS=True", "SMTP_SSL=False"),
            _file(
                "backend/app/core/config.py",
                "SMTP_PORT: int = 587",
                "SMTP_TLS: bool = True",
                "SMTP_SSL: bool = False",
            ),
        ),
    ),
    ClaimFact(
        "setup-project email and error-reporting settings",
        _SETUP_PROJECT_EMAIL,
        (
            "SMTP_HOST",
            "SMTP_USER",
            "SMTP_PASSWORD",
            "EMAILS_FROM_EMAIL",
            "SENTRY_DSN",
            "changes take effect after an application restart",
        ),
        (
            _file(
                ".env",
                "SMTP_HOST=",
                "SMTP_USER=",
                "SMTP_PASSWORD=",
                "EMAILS_FROM_EMAIL=",
                "SENTRY_DSN=",
            ),
            _file(
                "compose.yml",
                "SMTP_HOST: ${SMTP_HOST}",
                "SMTP_USER: ${SMTP_USER}",
                "SMTP_PASSWORD: ${SMTP_PASSWORD}",
                "EMAILS_FROM_EMAIL: ${EMAILS_FROM_EMAIL}",
                "SENTRY_DSN: ${SENTRY_DSN}",
            ),
            _file(
                "backend/app/utils.py",
                "settings.SMTP_HOST",
                "settings.SMTP_PORT",
                "settings.SMTP_TLS",
                "settings.SMTP_SSL",
                "settings.SMTP_USER",
                "settings.SMTP_PASSWORD",
                "settings.EMAILS_FROM_EMAIL",
                "message.send",
            ),
            _file(
                "backend/app/main.py",
                "if settings.SENTRY_DSN and settings.ENVIRONMENT != \"local\"",
                "sentry_sdk.init(dsn=str(settings.SENTRY_DSN)",
            ),
            _file("backend/app/core/config.py", "settings = Settings()"),
        ),
    ),
    ClaimFact(
        "setup-project deployment boundary",
        _SETUP_PROJECT_SKILL,
        (
            "Do not ask for the deployment domain, frontend host, CORS origins, "
            "environment name, or container image variables",
            "The generated local values are already wired into the backend and "
            "Compose configuration",
            "Container image variables are not present in this template's `.env`",
            "Point deployment work to `deployment.md` instead",
        ),
        (
            _file(
                ".env",
                "DOMAIN=",
                "FRONTEND_HOST=",
                "ENVIRONMENT=",
                "BACKEND_CORS_ORIGINS=",
            ),
            _file(
                "compose.yml",
                "FRONTEND_HOST: ${FRONTEND_HOST?Variable not set}",
                "ENVIRONMENT: ${ENVIRONMENT}",
                "BACKEND_CORS_ORIGINS: ${BACKEND_CORS_ORIGINS}",
                "traefik.http.routers.backend-http.rule=Host(`${DOMAIN?Variable not set}`)",
            ),
            _file(
                "backend/app/core/config.py",
                "FRONTEND_HOST: str",
                "ENVIRONMENT: Literal",
                "BACKEND_CORS_ORIGINS: Annotated",
                "self.BACKEND_CORS_ORIGINS",
                "self.FRONTEND_HOST",
            ),
            _file(
                "backend/app/main.py",
                "settings.ENVIRONMENT",
                "settings.all_cors_origins",
            ),
            _file(
                "deployment.md",
                "Set the `ENVIRONMENT`",
                "Set the `DOMAIN`",
                "`BACKEND_CORS_ORIGINS`",
            ),
        ),
        (_file(".env", "DOCKER_IMAGE_BACKEND=", "DOCKER_IMAGE_FRONTEND="),),
    ),
)

_STACK_SENTENCE = (
    "Every generated project is FastAPI, React, PostgreSQL, and Docker Compose"
)
_STACK_SOURCES = (
    STACK_FACTS["FastAPI"],
    STACK_FACTS["React"],
    STACK_FACTS["PostgreSQL"],
    STACK_FACTS["Docker Compose"],
)

REPOSITORY_CLAIM_FACTS = (
    ClaimFact(
        "Generation Skill fixed stack",
        "skills/dev-ready/SKILL.md",
        (
            "Every dev-ready project uses FastAPI, React, PostgreSQL, and "
            "Docker Compose",
            "Every dev-ready project has a frontend",
            "The frontend is React",
        ),
        _STACK_SOURCES,
        claim_root="repository",
    ),
    ClaimFact(
        "README stack sentence",
        "README.md",
        (_STACK_SENTENCE,),
        _STACK_SOURCES,
        claim_root="repository",
    ),
    ClaimFact(
        "PyPI README stack sentence",
        "README-pypi.md",
        (_STACK_SENTENCE,),
        _STACK_SOURCES,
        claim_root="repository",
    ),
)

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


# FR-38's login disclosure. The generated `README.md` tells the user which email
# to log in with, and the generation report says the same thing from a constant
# in `dev_ready.report.render`. Neither is derived from anything: the address is
# upstream's own `first_superuser` default in `copier.yml`, and `_template_data`
# deliberately does not override it. If upstream changes that default, both
# surfaces go stale in silence and the user is told to log in as somebody who
# does not exist.
#
# The generated `.env` carries the resolved answer, so the check needs no
# network and belongs here, in the guard that already runs against a real
# generated project immediately after generation. The renderer's constant is
# held to the README template by an offline test in tests/unit/test_report.py,
# which is what makes checking the README here cover both surfaces.
_SUPERUSER_EMAIL_KEY = "FIRST_SUPERUSER"
_EMAIL_IN_BACKTICKS = re.compile(r"`([^`\s@]+@[^`\s]+)`")

_FACT_SECTIONS = frozenset({"Stack", "Commands", "Repo layout", "Standards Source"})
_NON_FACTUAL_CAPITALIZED_TERMS = frozenset({"A", "Never", "The"})
_NON_FACTUAL_LOWERCASE_FACTS = frozenset({"hand-edit", "local-dev", "type-check"})
_NON_FACTUAL_INTRO_FACTS = frozenset(
    {"dev-ready", "full-stack", "github.com", "github.com/moofonli/dev-ready"}
)
_NON_FACTUAL_INTRO_WORDS = frozenset(
    {
        "by",
        "is",
        "of",
        "on",
        "project",
        "ready",
        "scaffolded",
        "template",
        "top",
        "together",
        "wired",
    }
)
_NON_FACTUAL_LOWERCASE_WORDS = frozenset(
    {
        "a",
        "adds",
        "an",
        "and",
        "bash",
        "build",
        "change",
        "check",
        "checks",
        "client",
        "cd",
        "database",
        "dev",
        "development",
        "down",
        "edit",
        "floor",
        "for",
        "from",
        "full",
        "generated",
        "generation",
        "hand",
        "hook",
        "install",
        "layout",
        "live",
        "local",
        "main",
        "migration",
        "migrations",
        "mirror",
        "model",
        "models",
        "never",
        "or",
        "orchestration",
        "overrides",
        "package's",
        "p",
        "proxy",
        "regenerate",
        "reload",
        "repository",
        "required",
        "requires",
        "reverse",
        "root",
        "run",
        "script",
        "serve",
        "services",
        "stack",
        "start",
        "stop",
        "strict",
        "test",
        "tests",
        "the",
        "them",
        "then",
        "tree",
        "type",
        "up",
        "upstream",
        "use",
        "uv",
        "watch",
        "with",
        "write",
        "bunx",
        "d",
        "form",
    }
)
_CAPITALIZED_TERM = re.compile(r"\b[A-Z][A-Za-z0-9]*(?:[/-][A-Za-z0-9]+)*\b")
_LOWERCASE_WORD = re.compile(r"\b[a-z][a-z0-9']*\b")
_LOWERCASE_FACT = re.compile(
    r"(?<![a-z0-9_])(?:[a-z0-9]+/|[a-z0-9]+(?:[-/.][a-z0-9]+)+)(?![a-z0-9_])"
)


def _claim_is_present(claim: str, text: str) -> bool:
    """Match a claim without accepting a longer tool or command token."""
    pattern = rf"(?<![A-Za-z0-9_-]){re.escape(claim.casefold())}(?![A-Za-z0-9_-])"
    return re.search(pattern, text.casefold()) is not None


def _contains_all_needles(text: str, needles: Sequence[str]) -> bool:
    """Match authored/source phrases without making line wrapping significant."""
    normalized = " ".join(text.casefold().split())
    return all(" ".join(needle.casefold().split()) in normalized for needle in needles)


def _source_fact_problem(project_dir: Path, source: SourceFact) -> str | None:
    """Describe why required source evidence fails, or return None."""
    source_path = project_dir / Path(source.path)
    if source.kind == "directory":
        return None if source_path.is_dir() else f"upstream source missing: {source.path}"
    if not source_path.is_file():
        return f"upstream source missing: {source.path}"
    if not source.needles:
        return None
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return f"upstream source unreadable: {source.path}"
    if not _contains_all_needles(source_text, source.needles):
        return f"upstream evidence missing from {source.path}"
    return None


def _source_fact_holds(project_dir: Path, source: SourceFact) -> bool:
    return _source_fact_problem(project_dir, source) is None


def _forbidden_source_problem(project_dir: Path, source: SourceFact) -> str | None:
    """Describe why forbidden-evidence checking fails, or return None."""
    source_path = project_dir / Path(source.path)
    if not source_path.is_file():
        return f"forbidden-evidence source missing: {source.path}"
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return f"forbidden-evidence source unreadable: {source.path}"
    normalized = " ".join(source_text.casefold().split())
    if any(
        " ".join(needle.casefold().split()) in normalized for needle in source.needles
    ):
        return f"forbidden upstream evidence present in {source.path}"
    return None


def _claim_failures(
    project_dir: Path,
    repository_root: Path,
    facts: Sequence[ClaimFact],
) -> list[str]:
    failures: list[str] = []
    for fact in facts:
        claim_root = repository_root if fact.claim_root == "repository" else project_dir
        claim_path = claim_root / fact.claim_path
        if not claim_path.is_file():
            failures.append(
                f"{fact.label}: authored claim file missing: {fact.claim_path}"
            )
            continue
        try:
            claim_text = claim_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            failures.append(
                f"{fact.label}: authored claim file unreadable: {fact.claim_path}"
            )
            continue
        if not _contains_all_needles(claim_text, fact.claim_needles):
            failures.append(
                f"{fact.label}: authored claim missing from {fact.claim_path}"
            )
            continue
        for source in fact.sources:
            if problem := _source_fact_problem(project_dir, source):
                failures.append(f"{fact.label}: {problem}")
        for source in fact.forbidden_sources:
            if problem := _forbidden_source_problem(project_dir, source):
                failures.append(f"{fact.label}: {problem}")
    return failures


def _is_mapped_term(term: str) -> bool:
    return any(
        _claim_is_present(term, claim) or _claim_is_present(claim, term) for claim in STACK_FACTS
    )


def _unmapped_structured_facts(section: str, bullet: str) -> list[str]:
    if section == "Stack":
        _, separator, facts = bullet.partition(":")
        if not separator:
            return []
        facts = facts.rsplit(" - ", 1)[0]
    elif section == "Repo layout":
        _, separator, facts = bullet.partition(" - ")
        if not separator or not any(_claim_is_present(claim, facts) for claim in STACK_FACTS):
            return []
    else:
        return []

    fragments = [fragment.strip(" `*.") for fragment in facts.split(",")]
    return [
        fragment
        for fragment in fragments
        if fragment and not any(_claim_is_present(claim, fragment) for claim in STACK_FACTS)
    ]


def _unmapped_intro_facts(agents_text: str) -> list[str]:
    if "## Stack" not in agents_text:
        return []

    intro = agents_text.split("## Stack", 1)[0]
    unknown: list[str] = []
    for line in intro.splitlines():
        statement = line.strip()
        if not statement or statement.startswith("#"):
            continue
        if " is " in statement:
            statement = statement.split(" is ", 1)[1]
        statement = re.sub(r"https?://\S+", "", statement)
        unknown_facts = [
            fact
            for fact in _LOWERCASE_FACT.findall(statement.casefold())
            if fact not in _NON_FACTUAL_INTRO_FACTS and not _is_mapped_term(fact)
        ]
        if unknown_facts:
            unknown.extend(unknown_facts)
            continue
        unknown_terms = [
            term
            for term in _CAPITALIZED_TERM.findall(statement)
            if term not in _NON_FACTUAL_CAPITALIZED_TERMS and not _is_mapped_term(term)
        ]
        if unknown_terms:
            unknown.append(" ".join(unknown_terms))
            continue
        unknown_words = [
            word
            for word in _LOWERCASE_WORD.findall(statement.casefold())
            if word not in _NON_FACTUAL_INTRO_WORDS
            and word not in _NON_FACTUAL_LOWERCASE_WORDS
            and not _is_mapped_term(word)
        ]
        unknown.extend(unknown_words)
    return [f"unmapped AGENTS.md claim: {fact}" for fact in unknown]


def _unmapped_fact_bullets(agents_text: str) -> list[str]:
    """Find factual bullets that are absent from the claim-to-source map."""
    section: str | None = None
    unmapped: list[str] = []
    for line in agents_text.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
            section = heading if heading in _FACT_SECTIONS else None
            continue
        if section is None:
            continue
        bullet = line.strip()
        if not bullet.startswith("- "):
            continue
        if not any(_claim_is_present(claim, bullet) for claim in STACK_FACTS):
            unmapped.append(f"unmapped AGENTS.md claim: {bullet}")
            continue
        structured_facts = _unmapped_structured_facts(section, bullet)
        if structured_facts:
            unmapped.extend(f"unmapped AGENTS.md claim: {fact}" for fact in structured_facts)
            continue
        lowercase_facts = [
            fact
            for fact in _LOWERCASE_FACT.findall(bullet.casefold())
            if fact not in _NON_FACTUAL_LOWERCASE_FACTS and not _is_mapped_term(fact)
        ]
        if lowercase_facts:
            unmapped.extend(f"unmapped AGENTS.md claim: {fact}" for fact in lowercase_facts)
            continue
        lowercase_words = [
            word
            for word in _LOWERCASE_WORD.findall(bullet.casefold())
            if word not in _NON_FACTUAL_LOWERCASE_WORDS and not _is_mapped_term(word)
        ]
        if lowercase_words:
            unmapped.extend(f"unmapped AGENTS.md claim: {word}" for word in lowercase_words)
            continue
        unknown_terms = [
            term
            for term in _CAPITALIZED_TERM.findall(bullet)
            if term not in _NON_FACTUAL_CAPITALIZED_TERMS and not _is_mapped_term(term)
        ]
        if unknown_terms:
            unmapped.append(f"unmapped AGENTS.md claim: {' '.join(unknown_terms)}")
    return unmapped


def _env_value(env_text: str, key: str) -> str | None:
    """Return the value of `key` in a dotenv file, or None when it is absent."""
    for raw in env_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        if separator and name.strip() == key:
            return value.strip().strip("\"'")
    return None


def _superuser_disclosure_failures(project_dir: Path) -> list[str]:
    """Return the ways the generated login disclosure disagrees with `.env`.

    The `.env` value is the truth: it is what upstream's template resolved the
    superuser email to at the pinned commit. Anything dev-ready states about it
    must match, and a missing file is a failure rather than a silent pass —
    a guard that cannot read its evidence has not checked anything.
    """
    env_path = project_dir / ".env"
    try:
        env_text = env_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return [
            "the generated .env is missing or unreadable, so the superuser email "
            "disclosed by README.md and the generation report cannot be checked"
        ]

    resolved = _env_value(env_text, _SUPERUSER_EMAIL_KEY)
    if not resolved:
        return [
            f"the generated .env has no {_SUPERUSER_EMAIL_KEY} value; upstream may have "
            "renamed or dropped the question, and the login disclosure in README.md "
            "and the generation report now describes nothing"
        ]

    try:
        readme_text = (project_dir / "README.md").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ["README.md is missing or unreadable"]

    disclosed = _EMAIL_IN_BACKTICKS.search(readme_text)
    if disclosed is None:
        return [
            f"README.md discloses no superuser email, but the generated .env resolved "
            f"{_SUPERUSER_EMAIL_KEY} to {resolved!r}; the first-login section is stale"
        ]
    if disclosed.group(1) != resolved:
        return [
            f"README.md discloses the superuser email {disclosed.group(1)!r}, but the "
            f"generated .env resolved {_SUPERUSER_EMAIL_KEY} to {resolved!r}; update the "
            "README template and the generation report's constant together"
        ]
    return []


def check_stack_facts(
    project_dir: Path, *, repository_root: Path | None = None
) -> list[str]:
    """Return dev-ready-authored claims that do not hold in project_dir."""
    if repository_root is None:
        repository_root = _REPOSITORY_ROOT
    agents_path = project_dir / "AGENTS.md"
    if not agents_path.is_file():
        return ["AGENTS.md is missing"]

    try:
        agents_source = agents_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ["AGENTS.md is unreadable"]

    agents_text = agents_source.casefold()
    failures = _unmapped_intro_facts(agents_source)
    failures.extend(_unmapped_fact_bullets(agents_source))
    for claim, source in STACK_FACTS.items():
        if not _claim_is_present(claim, agents_text):
            failures.append(claim)
            continue

        if not _source_fact_holds(project_dir, source):
            failures.append(claim)

    failures.extend(_superuser_disclosure_failures(project_dir))
    failures.extend(
        _claim_failures(project_dir, repository_root, REPOSITORY_CLAIM_FACTS)
    )
    if (project_dir / ".env").is_file():
        failures.extend(_claim_failures(project_dir, repository_root, SETUP_PROJECT_FACTS))
    return failures


def main(argv: Sequence[str] | None = None) -> int:
    """Run the stack-facts check for one generated project directory."""
    parser = argparse.ArgumentParser(
        description=(
            "Check dev-ready-authored upstream claims against the generated project tree."
        )
    )
    parser.add_argument(
        "project_dir",
        nargs="?",
        type=Path,
        default=Path("."),
        help="generated project directory (default: current directory)",
    )
    args = parser.parse_args(argv)

    failures = check_stack_facts(args.project_dir)
    if failures:
        print("Stack facts drift detected:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Stack facts match the pinned upstream tree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
