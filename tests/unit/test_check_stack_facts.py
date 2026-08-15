"""Offline tests for scripts/check_stack_facts.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

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
_SETUP_PROJECT = """\
The backend creates the superuser on first start and looks it up by email.
The startup initializer runs on every start.
FIRST_SUPERUSER and FIRST_SUPERUSER_PASSWORD are required settings and cannot simply be deleted.
Do not ask for the deployment domain, frontend host, CORS origins, environment name, or container image variables.
The generated local values are already wired into the backend and Compose configuration.
Container image variables are not present in this template's `.env`.
Point deployment work to `deployment.md` instead.
"""
_EMAIL_AND_ERROR_REPORTING = """\
SMTP_HOST SMTP_USER SMTP_PASSWORD EMAILS_FROM_EMAIL SENTRY_DSN
SMTP_PORT=587 SMTP_TLS=True SMTP_SSL=False
Email and error-reporting changes take effect after an application restart.
"""


def _write_project(
    tmp_path: Path,
    *,
    agents: str = _AGENTS,
    env_email: str | None = _UPSTREAM_SUPERUSER_EMAIL,
    readme_email: str | None = _UPSTREAM_SUPERUSER_EMAIL,
) -> Path:
    project = tmp_path / "project"
    (project / "backend" / "scripts").mkdir(parents=True)
    (project / "backend" / "app" / "core").mkdir(parents=True)
    (project / "backend" / "app" / "alembic").mkdir(parents=True)
    (project / "backend" / "tests").mkdir()
    (project / "frontend" / "src" / "client").mkdir(parents=True)
    (project / ".github" / "workflows").mkdir(parents=True)
    (project / ".agents" / "skills" / "setup-project").mkdir(parents=True)

    (project / "AGENTS.md").write_text(agents, encoding="utf-8")
    readme_login = f"- **Email**: `{readme_email}`\n" if readme_email else ""
    (project / "README.md").write_text(
        "https://github.com/fastapi/full-stack-fastapi-template\n" + readme_login,
        encoding="utf-8",
    )
    if env_email is not None:
        (project / ".env").write_text(
            f"SECRET_KEY=generated\nFIRST_SUPERUSER={env_email}\n"
            "FIRST_SUPERUSER_PASSWORD=generated\n"
            "SMTP_HOST=\nSMTP_USER=\nSMTP_PASSWORD=\n"
            "EMAILS_FROM_EMAIL=info@example.com\n"
            "SMTP_TLS=True\nSMTP_SSL=False\nSMTP_PORT=587\n"
            "SENTRY_DSN=\nDOMAIN=localhost\nFRONTEND_HOST=http://localhost:5173\n"
            "ENVIRONMENT=local\nBACKEND_CORS_ORIGINS=http://localhost\n",
            encoding="utf-8",
        )
    (project / ".agents" / "skills" / "setup-project" / "SKILL.md").write_text(
        _SETUP_PROJECT,
        encoding="utf-8",
    )
    (
        project
        / ".agents"
        / "skills"
        / "setup-project"
        / "email-and-error-reporting.md"
    ).write_text(_EMAIL_AND_ERROR_REPORTING, encoding="utf-8")
    (project / "backend" / "pyproject.toml").write_text(
        """\
dependencies = ["fastapi", "sqlmodel", "psycopg", "pydantic", "alembic"]
dev = ["pytest", "mypy", "ty", "ruff", "coverage"]
strict = true
""",
        encoding="utf-8",
    )
    (project / "backend" / "app" / "main.py").write_text(
        "from fastapi import FastAPI\n"
        "import sentry_sdk\n"
        "from app.core.config import settings\n\n"
        "if settings.SENTRY_DSN and settings.ENVIRONMENT != \"local\":\n"
        "    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)\n\n"
        "if settings.all_cors_origins:\n"
        "    allow_origins=settings.all_cors_origins\n\n"
        "app = FastAPI()\n",
        encoding="utf-8",
    )
    (project / "backend" / "app" / "utils.py").write_text(
        "mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL)\n"
        "smtp_options = {\"host\": settings.SMTP_HOST, \"port\": settings.SMTP_PORT}\n"
        "if settings.SMTP_TLS:\n"
        "    smtp_options[\"tls\"] = True\n"
        "elif settings.SMTP_SSL:\n"
        "    smtp_options[\"ssl\"] = True\n"
        "if settings.SMTP_USER:\n"
        "    smtp_options[\"user\"] = settings.SMTP_USER\n"
        "if settings.SMTP_PASSWORD:\n"
        "    smtp_options[\"password\"] = settings.SMTP_PASSWORD\n"
        "message.send(to=email_to, smtp=smtp_options)\n",
        encoding="utf-8",
    )
    (project / "backend" / "app" / "models.py").write_text(
        "from sqlmodel import SQLModel\n",
        encoding="utf-8",
    )
    (project / "backend" / "app" / "core" / "config.py").write_text(
        'FRONTEND_HOST: str = "http://localhost:5173"\n'
        'ENVIRONMENT: Literal["local", "staging", "production"] = "local"\n'
        "BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, "
        "BeforeValidator(parse_cors)] = []\n"
        "def all_cors_origins(self) -> list[str]:\n"
        "    return self.BACKEND_CORS_ORIGINS + [self.FRONTEND_HOST]\n"
        "FIRST_SUPERUSER: EmailStr\n"
        "FIRST_SUPERUSER_PASSWORD: str\n"
        "SMTP_TLS: bool = True\nSMTP_SSL: bool = False\nSMTP_PORT: int = 587\n"
        "SMTP_HOST: str | None = None\nSMTP_USER: str | None = None\n"
        "SMTP_PASSWORD: str | None = None\nEMAILS_FROM_EMAIL: EmailStr | None = None\n"
        "SENTRY_DSN: HttpUrl | None = None\n"
        "settings = Settings()\n",
        encoding="utf-8",
    )
    (project / "backend" / "app" / "core" / "db.py").write_text(
        "select(User).where(User.email == settings.FIRST_SUPERUSER)\n"
        "if not user:\n"
        "password=settings.FIRST_SUPERUSER_PASSWORD\n"
        "is_superuser=True\n",
        encoding="utf-8",
    )
    script_contents = {
        "prestart.sh": (
            "#!/bin/sh\nalembic upgrade head\npython app/initial_data.py\n"
        ),
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
    (project / "compose.yml").write_text(
        "services:\n"
        "  db:\n"
        "  traefik:\n"
        "  prestart:\n"
        "    command: bash scripts/prestart.sh\n"
        "    environment:\n"
        "      FRONTEND_HOST: ${FRONTEND_HOST?Variable not set}\n"
        "      ENVIRONMENT: ${ENVIRONMENT}\n"
        "      BACKEND_CORS_ORIGINS: ${BACKEND_CORS_ORIGINS}\n"
        "      FIRST_SUPERUSER: ${FIRST_SUPERUSER?Variable not set}\n"
        "      FIRST_SUPERUSER_PASSWORD: ${FIRST_SUPERUSER_PASSWORD?Variable not set}\n"
        "      SMTP_HOST: ${SMTP_HOST}\n"
        "      SMTP_USER: ${SMTP_USER}\n"
        "      SMTP_PASSWORD: ${SMTP_PASSWORD}\n"
        "      EMAILS_FROM_EMAIL: ${EMAILS_FROM_EMAIL}\n"
        "      SENTRY_DSN: ${SENTRY_DSN}\n"
        "  backend:\n"
        "    depends_on:\n"
        "      prestart:\n"
        "        condition: service_completed_successfully\n"
        "    labels:\n"
        "      - traefik.http.routers.backend-http.rule=Host(`${DOMAIN?Variable not set}`)\n",
        encoding="utf-8",
    )
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
    (project / "deployment.md").write_text(
        "# Deployment\nSet the `ENVIRONMENT`.\nSet the `DOMAIN`.\n"
        "Configure `BACKEND_CORS_ORIGINS`.\n",
        encoding="utf-8",
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
    main = project / "backend" / "app" / "main.py"
    main.write_text(
        main.read_text(encoding="utf-8").replace("app = FastAPI()", "app = object()"),
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
    env_path = project / ".env"
    env_path.write_text(
        "\n".join(
            line
            for line in env_path.read_text(encoding="utf-8").splitlines()
            if not line.startswith("FIRST_SUPERUSER=")
        )
        + "\n",
        encoding="utf-8",
    )

    failures = check_stack_facts.check_stack_facts(project)

    assert len(failures) == 1
    assert "FIRST_SUPERUSER" in failures[0]


def test_setup_project_smtp_defaults_drift_is_reported(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    env_path = project / ".env"
    env_path.write_text(
        env_path.read_text(encoding="utf-8").replace("SMTP_PORT=587", "SMTP_PORT=465"),
        encoding="utf-8",
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "setup-project SMTP defaults: upstream evidence missing from .env"
    ]


def test_setup_project_authored_smtp_claim_drift_is_reported(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    guidance = (
        project
        / ".agents"
        / "skills"
        / "setup-project"
        / "email-and-error-reporting.md"
    )
    guidance.write_text(
        guidance.read_text(encoding="utf-8").replace("SMTP_PORT=587", "SMTP_PORT=465"),
        encoding="utf-8",
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "setup-project SMTP defaults: generated claim missing from "
        ".agents/skills/setup-project/email-and-error-reporting.md"
    ]


def test_setup_project_superuser_initializer_drift_is_reported(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    prestart = project / "backend" / "scripts" / "prestart.sh"
    prestart.write_text(
        prestart.read_text(encoding="utf-8").replace("python app/initial_data.py\n", ""),
        encoding="utf-8",
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "setup-project superuser lifecycle: upstream evidence missing from "
        "backend/scripts/prestart.sh"
    ]


def test_setup_project_required_superuser_setting_drift_is_reported(
    tmp_path: Path,
) -> None:
    project = _write_project(tmp_path)
    config = project / "backend" / "app" / "core" / "config.py"
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "FIRST_SUPERUSER_PASSWORD: str\n", ""
        ),
        encoding="utf-8",
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "setup-project required superuser settings: upstream evidence missing from "
        "backend/app/core/config.py"
    ]


def test_setup_project_error_reporting_setting_drift_is_reported(
    tmp_path: Path,
) -> None:
    project = _write_project(tmp_path)
    compose = project / "compose.yml"
    compose.write_text(
        compose.read_text(encoding="utf-8").replace(
            "      SENTRY_DSN: ${SENTRY_DSN}\n", ""
        ),
        encoding="utf-8",
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "setup-project email and error-reporting settings: upstream evidence missing "
        "from compose.yml"
    ]


def test_setup_project_email_runtime_consumption_drift_is_reported(
    tmp_path: Path,
) -> None:
    project = _write_project(tmp_path)
    utils = project / "backend" / "app" / "utils.py"
    utils.write_text(
        utils.read_text(encoding="utf-8").replace(
            '"host": settings.SMTP_HOST', '"host": "localhost"'
        ),
        encoding="utf-8",
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "setup-project email and error-reporting settings: upstream evidence missing "
        "from backend/app/utils.py"
    ]


def test_setup_project_sentry_runtime_consumption_drift_is_reported(
    tmp_path: Path,
) -> None:
    project = _write_project(tmp_path)
    main = project / "backend" / "app" / "main.py"
    main.write_text(
        main.read_text(encoding="utf-8").replace(
            "    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)\n",
            "    pass\n",
        ),
        encoding="utf-8",
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "setup-project email and error-reporting settings: upstream evidence missing "
        "from backend/app/main.py"
    ]


def test_setup_project_deployment_reference_drift_is_reported(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    (project / "deployment.md").unlink()

    assert check_stack_facts.check_stack_facts(project) == [
        "setup-project deployment boundary: upstream source missing: deployment.md"
    ]


def test_setup_project_local_value_runtime_consumption_drift_is_reported(
    tmp_path: Path,
) -> None:
    project = _write_project(tmp_path)
    main = project / "backend" / "app" / "main.py"
    main.write_text(
        main.read_text(encoding="utf-8").replace(
            "if settings.all_cors_origins:\n"
            "    allow_origins=settings.all_cors_origins\n\n",
            "",
        ),
        encoding="utf-8",
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "setup-project deployment boundary: upstream evidence missing from "
        "backend/app/main.py"
    ]


def test_setup_project_absent_image_variables_drift_is_reported(tmp_path: Path) -> None:
    project = _write_project(tmp_path)
    env_path = project / ".env"
    env_path.write_text(
        env_path.read_text(encoding="utf-8") + "DOCKER_IMAGE_BACKEND=backend\n",
        encoding="utf-8",
    )

    assert check_stack_facts.check_stack_facts(project) == [
        "setup-project deployment boundary: forbidden upstream evidence present in .env"
    ]


def test_unreadable_generated_claim_file_has_an_accurate_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _write_project(tmp_path)
    target = project / ".agents" / "skills" / "setup-project" / "SKILL.md"
    original_read_text = Path.read_text

    def read_text(path: Path, *args: object, **kwargs: object) -> str:
        if path == target:
            raise PermissionError("simulated unreadable file")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)

    failures = check_stack_facts.check_stack_facts(project)

    assert failures == [
        "setup-project superuser lifecycle: generated claim file unreadable: "
        ".agents/skills/setup-project/SKILL.md",
        "setup-project required superuser settings: generated claim file unreadable: "
        ".agents/skills/setup-project/SKILL.md",
        "setup-project deployment boundary: generated claim file unreadable: "
        ".agents/skills/setup-project/SKILL.md",
    ]


def test_non_utf8_generated_claim_file_has_an_accurate_diagnostic(
    tmp_path: Path,
) -> None:
    project = _write_project(tmp_path)
    target = project / ".agents" / "skills" / "setup-project" / "SKILL.md"
    target.write_bytes(b"\xff")

    failures = check_stack_facts.check_stack_facts(project)

    assert failures == [
        "setup-project superuser lifecycle: generated claim file unreadable: "
        ".agents/skills/setup-project/SKILL.md",
        "setup-project required superuser settings: generated claim file unreadable: "
        ".agents/skills/setup-project/SKILL.md",
        "setup-project deployment boundary: generated claim file unreadable: "
        ".agents/skills/setup-project/SKILL.md",
    ]


def test_unreadable_forbidden_source_is_not_reported_as_forbidden_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _write_project(tmp_path)
    target = project / ".env"
    original_read_text = Path.read_text

    def read_text(path: Path, *args: object, **kwargs: object) -> str:
        if path == target:
            raise PermissionError("simulated unreadable file")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)

    failures = check_stack_facts.check_stack_facts(project)

    assert (
        "setup-project deployment boundary: forbidden-evidence source unreadable: .env"
        in failures
    )
    assert not any("forbidden upstream evidence present" in failure for failure in failures)
