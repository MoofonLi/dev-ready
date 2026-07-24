"""Deep module for the complete lifecycle of catalog-item injected effects."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

SUPPORTED_EFFECT_KINDS = ("mcp-server", "npm-dev-dependency")


class CatalogEffectError(Exception):
    """An effect definition or local-project operation is invalid."""


class _EffectItem(Protocol):
    id: str
    effect: CatalogEffect | None


class _Selection(Protocol):
    def items(self, name: str) -> frozenset[str]: ...


@dataclass(frozen=True)
class SharedTargets:
    """All shared targets and the subset owned by the current selection."""

    all: frozenset[str]
    selected: frozenset[str]


@dataclass(frozen=True)
class CatalogEffect(ABC):
    """Validated effect with application and observation behind one interface."""

    target: str
    _location: str

    @abstractmethod
    def apply(self, project_dir: Path) -> None:
        """Apply the effect to its shared local target."""

    @abstractmethod
    def is_present(self, project_dir: Path) -> bool:
        """Observe whether the complete effect is present."""

    def _read_target(self, project_dir: Path) -> tuple[Path, dict[str, object]]:
        target_path = self._target_path(project_dir)
        if not target_path.exists():
            raise CatalogEffectError(
                f"{self._location} requires target {self.target!r}, but it is missing"
            )
        try:
            data = json.loads(target_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise CatalogEffectError(f"failed to parse {self.target}: {error}") from error
        if not isinstance(data, dict):
            raise CatalogEffectError(f"{self.target} root must be a JSON object")
        return target_path, data

    def _target_path(self, project_dir: Path) -> Path:
        try:
            root = project_dir.resolve()
            target_path = project_dir / self.target
            current = project_dir
            for part in Path(self.target).parts:
                current = current / part
                if current.is_symlink():
                    raise CatalogEffectError(
                        f"unsafe target {self.target!r}: symlink traversal is not allowed"
                    )
            resolved = target_path.resolve()
        except (OSError, RuntimeError) as error:
            raise CatalogEffectError(f"unsafe target {self.target!r}: {error}") from error
        if resolved != root and root not in resolved.parents:
            raise CatalogEffectError(
                f"unsafe target {self.target!r}: path escapes the local project"
            )
        return target_path

    def _write_target(self, target_path: Path, data: dict[str, object]) -> None:
        try:
            target_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        except OSError as error:
            raise CatalogEffectError(f"failed to write {self.target}: {error}") from error


@dataclass(frozen=True)
class _McpServerEffect(CatalogEffect):
    package: str
    pin: str
    server_name: str
    command: str

    def apply(self, project_dir: Path) -> None:
        target_path, data = self._read_target(project_dir)
        servers = data.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            raise CatalogEffectError(f"'mcpServers' field in {self.target} must be a JSON object")
        if self.server_name in servers:
            raise CatalogEffectError(
                f"server {self.server_name!r} already exists in {self.target}"
            )
        servers[self.server_name] = {
            "command": self.command,
            "args": [f"{self.package}=={self.pin}"],
        }
        self._write_target(target_path, data)

    def is_present(self, project_dir: Path) -> bool:
        target_path = self._target_path(project_dir)
        if not target_path.exists():
            return False
        _, data = self._read_target(project_dir)
        servers = data.get("mcpServers")
        if not isinstance(servers, dict):
            return False
        configured = servers.get(self.server_name)
        return (
            isinstance(configured, dict)
            and configured.get("command") == self.command
            and configured.get("args") == [f"{self.package}=={self.pin}"]
        )


@dataclass(frozen=True)
class _NpmDevDependencyEffect(CatalogEffect):
    package: str
    pin: str
    scripts: tuple[tuple[str, str], ...]

    def apply(self, project_dir: Path) -> None:
        target_path, data = self._read_target(project_dir)
        dependencies = data.setdefault("devDependencies", {})
        if not isinstance(dependencies, dict):
            raise CatalogEffectError(
                f"'devDependencies' in {self.target} must be a JSON object"
            )
        if self.package in dependencies:
            raise CatalogEffectError(
                f"package {self.package!r} already declared in {self.target} devDependencies"
            )
        dependencies[self.package] = self.pin

        scripts = data.setdefault("scripts", {})
        if not isinstance(scripts, dict):
            raise CatalogEffectError(f"'scripts' in {self.target} must be a JSON object")
        for name, command in self.scripts:
            if name in scripts:
                raise CatalogEffectError(
                    f"script {name!r} already declared in {self.target} scripts"
                )
            scripts[name] = command
        self._write_target(target_path, data)

    def is_present(self, project_dir: Path) -> bool:
        target_path = self._target_path(project_dir)
        if not target_path.exists():
            return False
        _, data = self._read_target(project_dir)
        dependencies = data.get("devDependencies")
        scripts = data.get("scripts")
        return (
            isinstance(dependencies, dict)
            and dependencies.get(self.package) == self.pin
            and isinstance(scripts, dict)
            and all(scripts.get(name) == command for name, command in self.scripts)
        )


def classify_shared_targets(
    catalog: Mapping[str, Iterable[_EffectItem]],
    selection: _Selection,
) -> SharedTargets:
    """Classify effect-owned shared targets for lifecycle planning."""
    all_targets: set[str] = set()
    selected_targets: set[str] = set()
    for name, items in catalog.items():
        selected = selection.items(name) if name in {"skills", "mcp"} else frozenset()
        for item in items:
            if item.effect is None:
                continue
            all_targets.add(item.effect.target)
            if item.id in selected:
                selected_targets.add(item.effect.target)
    return SharedTargets(frozenset(all_targets), frozenset(selected_targets))


def parse_catalog_effect(
    raw: object,
    *,
    mode: str,
    pin: str | None,
    location: str,
) -> CatalogEffect | None:
    """Validate an effect definition and return its behavior-rich representation."""
    if raw is None:
        return None
    if mode != "pinned-dependency":
        raise CatalogEffectError(
            f"{location} field 'inject' is only allowed for pinned-dependency items"
        )
    if not isinstance(raw, dict):
        raise CatalogEffectError(f"{location} field 'inject' must be an object")
    if pin is None:
        raise CatalogEffectError(f"{location} with an injected effect requires a pin")

    kind = raw.get("kind")
    if not isinstance(kind, str) or kind not in SUPPORTED_EFFECT_KINDS:
        raise CatalogEffectError(
            f"{location} inject field 'kind' must be one of {SUPPORTED_EFFECT_KINDS!r}, got {kind!r}"
        )
    target = _relative_path(raw.get("target"), location, "target")
    package = _non_empty_string(raw.get("package"), location, "package")

    if kind == "mcp-server":
        if "scripts" in raw and raw.get("scripts") is not None:
            raise CatalogEffectError(
                f"{location} inject kind 'mcp-server' must not have 'scripts'"
            )
        return _McpServerEffect(
            target=target,
            _location=location,
            package=package,
            pin=pin,
            server_name=_non_empty_string(raw.get("server_name"), location, "server_name"),
            command=_non_empty_string(raw.get("command"), location, "command"),
        )

    if ("server_name" in raw and raw.get("server_name") is not None) or (
        "command" in raw and raw.get("command") is not None
    ):
        raise CatalogEffectError(
            f"{location} inject kind 'npm-dev-dependency' must not have 'server_name' or 'command'"
        )
    scripts_raw = raw.get("scripts")
    if not isinstance(scripts_raw, dict) or not scripts_raw:
        raise CatalogEffectError(
            f"{location} inject field 'scripts' must be a non-empty object"
        )
    scripts: list[tuple[str, str]] = []
    for name, command in scripts_raw.items():
        if not isinstance(name, str) or not name or not isinstance(command, str) or not command:
            raise CatalogEffectError(
                f"{location} inject script entry must be a non-empty string -> non-empty string mapping"
            )
        scripts.append((name, command))
    return _NpmDevDependencyEffect(
        target=target,
        _location=location,
        package=package,
        pin=pin,
        scripts=tuple(scripts),
    )


def _non_empty_string(value: object, location: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise CatalogEffectError(
            f"{location} inject field {field!r} must be a non-empty string"
        )
    return value


def _relative_path(value: object, location: str, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise CatalogEffectError(
            f"{location} path field {field!r} must be a non-empty string"
        )
    if (
        value.startswith("/")
        or value.startswith("\\")
        or "\\" in value
        or any(segment == ".." for segment in value.split("/"))
    ):
        raise CatalogEffectError(
            f"{location} path field {field!r} must be a relative path without '..', got {value!r}"
        )
    return value
