"""Offline tests for scripts/check_stack_facts.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_stack_facts.py"
_spec = importlib.util.spec_from_file_location("check_stack_facts", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
check_stack_facts = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_stack_facts)

_AGENTS = """\
FastAPI SQLModel PostgreSQL Pydantic Alembic
React TypeScript Vite Tailwind CSS shadcn/ui
TanStack Query TanStack Router TanStack Table react-hook-form zod
Docker Compose Traefik
database
docker compose watch db mailcatcher
scripts/prestart.sh scripts/tests-start.sh scripts/lint.sh scripts/format.sh
fastapi dev app/main.py bun install bun run dev pytest with coverage
biome check ./ biome format --write ./
pytest coverage ruff check ruff format mypy ty Bun Playwright biome tsc 90%
live services generated frontend API client client-generation script generated route tree Alembic migration
backend tests mirror FastAPI application React application SQLModel models Alembic migrations
Backend Frontend Infra
backend/ frontend/ app/main.py
compose.yml compose.override.yml
fastapi/full-stack-fastapi-template
tsconfig.build.json
"""


_UPSTREAM_SUPERUSER_EMAIL = "admin@example.com"


def _write_project(
    tmp_path: Path,
    *,
    agents: str = _AGENTS,
    env_email: str | None = _UPSTREAM_SUPERUSER_EMAIL,
    readme_email: str | None = _UPSTREAM_SUPERUSER_EMAIL,
) -> Path:
    project = tmp_path / "project"
    (project / "backend" / "scripts").mkdir(parents=True)
    (project / "backend" / "app" / "alembic").mkdir(parents=True)
    (project / "backend" / "tests").mkdir()
    (project / "frontend" / "src" / "client").mkdir(parents=True)
    (project / ".github" / "workflows").mkdir(parents=True)

    (project / "AGENTS.md").write_text(agents, encoding="utf-8")
    readme_login = f"- **Email**: `{readme_email}`\n" if readme_email else ""
    (project / "README.md").write_text(
        "https://github.com/fastapi/full-stack-fastapi-template\n" + readme_login,
        encoding="utf-8",
    )
    if env_email is not None:
        (project / ".env").write_text(
            f"SECRET_KEY=generated\nFIRST_SUPERUSER={env_email}\n"
            "FIRST_SUPERUSER_PASSWORD=generated\n",
            encoding="utf-8",
        )
    (project / "backend" / "pyproject.toml").write_text(
        """\
dependencies = ["fastapi", "sqlmodel", "psycopg", "pydantic", "alembic"]
dev = ["pytest", "mypy", "ty", "ruff", "coverage"]
strict = true
""",
        encoding="utf-8",
    )
    (project / "backend" / "app" / "main.py").write_text(
        "from fastapi import FastAPI\n\napp = FastAPI()\n",
        encoding="utf-8",
    )
    (project / "backend" / "app" / "models.py").write_text(
        "from sqlmodel import SQLModel\n",
        encoding="utf-8",
    )
    script_contents = {
        "prestart.sh": "#!/bin/sh\nalembic upgrade head\n",
        "tests-start.sh": "#!/bin/sh\nbash scripts/test.sh\n",
        "test.sh": "#!/bin/sh\ncoverage run -m pytest\n",
        "lint.sh": ("#!/bin/sh\nmypy app\nty check app\nruff check app\nruff format app --check\n"),
        "format.sh": "#!/bin/sh\nruff format app scripts\n",
    }
    for script, content in script_contents.items():
        (project / "backend" / "scripts" / script).write_text(content, encoding="utf-8")
    (project / "frontend" / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {
                    "react": "*",
                    "typescript": "*",
                    "vite": "*",
                    "tailwindcss": "*",
                    "@tanstack/react-query": "*",
                    "@tanstack/react-router": "*",
                    "@tanstack/react-table": "*",
                    "react-hook-form": "*",
                    "zod": "*",
                },
                "devDependencies": {
                    "@biomejs/biome": "*",
                    "@playwright/test": "*",
                },
                "scripts": {
                    "dev": "vite",
                    "build": "tsc -p tsconfig.build.json && vite build",
                    "generate-client": "openapi-ts",
                    "lint": "biome check --write --unsafe ./",
                    "test": "bunx playwright test",
                },
            }
        ),
        encoding="utf-8",
    )
    (project / "frontend" / "tsconfig.build.json").write_text(
        '{"compilerOptions": {"noEmit": true, "strict": true}}\n',
        encoding="utf-8",
    )
    (project / "frontend" / "components.json").write_text(
        '{"$schema": "https://ui.shadcn.com/schema.json"}\n', encoding="utf-8"
    )
    (project / "package.json").write_text('{"workspaces": ["frontend"]}\n', encoding="utf-8")
    (project / "bun.lock").write_text("bun lockfile\n", encoding="utf-8")
    (project / "compose.yml").write_text("services:\n  db:\n  traefik:\n", encoding="utf-8")
    (project / "compose.override.yml").write_text(
        "services:\n  db:\n  mailcatcher:\n  watch:\n", encoding="utf-8"
    )
    (project / ".github" / "workflows" / "test-backend.yml").write_text(
        "coverage report --fail-under=90\n", encoding="utf-8"
    )
    (project / "frontend" / "src" / "routeTree.gen.ts").write_text(
        "// generated\n", encoding="utf-8"
    )
    (project / "frontend" / "src" / "client" / "index.ts").write_text(
        "// generated\n", encoding="utf-8"
    )
    return project


def test_project_with_all_mapped_facts_is_clean(tmp_path: Path) -> None:
    assert check_stack_facts.check_stack_facts(_write_project(tmp_path)) == []


def test_missing_backend_type_checker_returns_only_that_claim(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    pyproject = project / "backend" / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8").replace('"mypy", ', ""), encoding="utf-8"
    )

    assert check_stack_facts.check_stack_facts(project) == ["mypy"]


def test_claim_matching_does_not_accept_longer_react_token(tmp_path: Path) -> None:
    agents = _AGENTS.replace("React", "reactive")

    assert check_stack_facts.check_stack_facts(_write_project(tmp_path, agents=agents)) == [
        "React",
        "React application",
    ]


def test_claim_matching_does_not_accept_longer_bun_token(tmp_path: Path) -> None:
    agents = _AGENTS.replace("Bun", "bunx").replace("bun ", "bunx ")

    assert check_stack_facts.check_stack_facts(_write_project(tmp_path, agents=agents)) == [
        "Bun",
        "bun install",
        "bun run dev",
    ]


def test_missing_backend_serve_target_returns_only_that_claim(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    (project / "backend" / "app" / "main.py").write_text(
        "from fastapi import FastAPI\n",
        encoding="utf-8",
    )

    assert check_stack_facts.check_stack_facts(project) == ["fastapi dev app/main.py"]


def test_missing_frontend_serve_script_returns_only_that_claim(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    package = project / "frontend" / "package.json"
    package.write_text(
        package.read_text(encoding="utf-8").replace('"dev": "vite"', '"dev": "missing"'),
        encoding="utf-8",
    )

    assert check_stack_facts.check_stack_facts(project) == ["bun run dev"]


def test_missing_backend_test_script_returns_only_that_claim(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    (project / "backend" / "scripts" / "test.sh").unlink()

    assert check_stack_facts.check_stack_facts(project) == ["pytest with coverage"]


def test_missing_frontend_tool_returns_only_that_claim(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    package = project / "frontend" / "package.json"
    package.write_text(
        package.read_text(encoding="utf-8").replace("playwright", "missing-tool"),
        encoding="utf-8",
    )

    assert check_stack_facts.check_stack_facts(project) == ["Playwright"]


def test_missing_upstream_script_returns_only_that_claim(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    (project / "backend" / "scripts" / "lint.sh").unlink()

    assert check_stack_facts.check_stack_facts(project) == [
        "scripts/lint.sh",
        "ruff check",
        "ruff format",
    ]


def test_missing_generated_claim_is_reported_in_the_reverse_direction(tmp_path: Path) -> None:
    project = _write_project(tmp_path, agents=_AGENTS.replace("TanStack Table ", ""))

    assert check_stack_facts.check_stack_facts(project) == ["TanStack Table"]


def test_unmapped_factual_bullet_is_reported(tmp_path: Path) -> None:
    project = _write_project(
        tmp_path,
        agents=_AGENTS + "\n## Stack\n\n- Mystery Tool\n",
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "unmapped AGENTS.md claim: - Mystery Tool"
    ]


def test_unmapped_embedded_fact_is_reported(tmp_path: Path) -> None:
    project = _write_project(
        tmp_path,
        agents=_AGENTS + "\n## Stack\n\n- **Frontend**: React, Mystery Tool\n",
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "unmapped AGENTS.md claim: Mystery Tool"
    ]


def test_unmapped_lowercase_embedded_fact_is_reported(tmp_path: Path) -> None:
    project = _write_project(
        tmp_path,
        agents=_AGENTS + "\n## Stack\n\n- **Frontend**: React, mystery-tool\n",
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "unmapped AGENTS.md claim: mystery-tool"
    ]


def test_unmapped_lowercase_command_fact_is_reported(tmp_path: Path) -> None:
    project = _write_project(
        tmp_path,
        agents=_AGENTS + "\n## Commands\n\n- Frontend tests: `mystery`\n",
    )

    assert check_stack_facts.check_stack_facts(project) == ["unmapped AGENTS.md claim: mystery"]


def test_unmapped_lowercase_standards_fact_is_reported(tmp_path: Path) -> None:
    project = _write_project(
        tmp_path,
        agents=(
            _AGENTS
            + "\n## Standards Source\n\n"
            + "- Never hand-edit the generated frontend API client with mystery.\n"
        ),
    )

    assert check_stack_facts.check_stack_facts(project) == ["unmapped AGENTS.md claim: mystery"]


def test_unmapped_intro_fact_is_reported(tmp_path: Path) -> None:
    project = _write_project(
        tmp_path,
        agents=("demo-app is a FastAPI project with mystery-tool.\n\n## Stack\n\n" + _AGENTS),
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "unmapped AGENTS.md claim: mystery-tool"
    ]


def test_unmapped_plain_intro_fact_is_reported(tmp_path: Path) -> None:
    project = _write_project(
        tmp_path,
        agents=("demo-app is a FastAPI project with mystery.\n\n## Stack\n\n" + _AGENTS),
    )

    assert check_stack_facts.check_stack_facts(project) == ["unmapped AGENTS.md claim: mystery"]


def test_unmapped_title_case_intro_fact_is_reported(tmp_path: Path) -> None:
    project = _write_project(
        tmp_path,
        agents=("demo-app is a FastAPI project with Mystery Tool.\n\n## Stack\n\n" + _AGENTS),
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "unmapped AGENTS.md claim: Mystery Tool"
    ]


def test_unknown_upstream_addition_does_not_require_generated_documentation(
    tmp_path: Path,
) -> None:
    project = _write_project(tmp_path)
    package = project / "frontend" / "package.json"
    package.write_text(
        package.read_text(encoding="utf-8").replace(
            '"react": "*"', '"react": "*", "new-tool": "*"'
        ),
        encoding="utf-8",
    )

    assert check_stack_facts.check_stack_facts(project) == []


def test_missing_agents_file_fails_loudly(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    (project / "AGENTS.md").unlink()

    assert check_stack_facts.check_stack_facts(project) == ["AGENTS.md is missing"]


def test_generated_client_claim_requires_a_directory(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    client_dir = project / "frontend" / "src" / "client"
    (client_dir / "index.ts").unlink()
    client_dir.rmdir()
    client_dir.write_text("not a directory\n", encoding="utf-8")

    assert check_stack_facts.check_stack_facts(project) == ["generated frontend API client"]


# FR-38's login disclosure states an email dev-ready does not choose: it is
# upstream's own `first_superuser` copier default, which `_template_data`
# deliberately does not override. The generated `.env` is where the resolved
# value lands, so it is the only thing in a generated project that can prove the
# disclosure still true.


def test_superuser_disclosure_matching_the_generated_env_is_clean(tmp_path: Path) -> None:
    assert check_stack_facts.check_stack_facts(_write_project(tmp_path)) == []


def test_upstream_changing_the_superuser_default_is_reported(tmp_path: Path) -> None:
    project = _write_project(tmp_path, env_email="root@example.com", readme_email=None)

    failures = check_stack_facts.check_stack_facts(project)

    assert len(failures) == 1
    assert "root@example.com" in failures[0]
    assert "README.md" in failures[0]


def test_readme_disclosing_a_stale_superuser_email_is_reported(tmp_path: Path) -> None:
    project = _write_project(tmp_path, readme_email="stale@example.com")

    failures = check_stack_facts.check_stack_facts(project)

    assert len(failures) == 1
    assert _UPSTREAM_SUPERUSER_EMAIL in failures[0]


def test_missing_env_fails_loudly_rather_than_passing_vacuously(tmp_path: Path) -> None:
    project = _write_project(tmp_path, env_email=None)

    failures = check_stack_facts.check_stack_facts(project)

    assert len(failures) == 1
    assert ".env" in failures[0]


def test_env_without_the_superuser_key_is_reported(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    (project / ".env").write_text("SECRET_KEY=generated\n", encoding="utf-8")

    failures = check_stack_facts.check_stack_facts(project)

    assert len(failures) == 1
    assert "FIRST_SUPERUSER" in failures[0]
