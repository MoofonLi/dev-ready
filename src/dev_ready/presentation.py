"""Render dev-ready's frameless Static Screen idiom."""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from typing import TextIO

from rich.console import Console
from rich.text import Text

__all__ = [
    "PresentationStyle",
    "ScreenBlock",
    "ScreenLine",
    "detect_presentation_style",
    "render_screen",
]


@dataclass(frozen=True)
class PresentationStyle:
    """Resolved colour and width values for one Static Screen."""

    color: bool = False
    width: int = 80


@dataclass(frozen=True)
class ScreenLine:
    """One literal output line, optionally eligible for prose wrapping."""

    text: str
    wrap: bool = True


@dataclass(frozen=True)
class ScreenBlock:
    """A heading and its ordered lines in one Static Screen block."""

    heading: str
    lines: tuple[ScreenLine, ...]


def detect_presentation_style(stream: TextIO) -> PresentationStyle:
    """Resolve Rich's terminal capabilities into primitive rendering values."""
    console = Console(file=stream)
    if not console.is_terminal:
        return PresentationStyle()
    return PresentationStyle(color=not console.no_color, width=console.width)


def render_screen(
    blocks: tuple[ScreenBlock, ...],
    *,
    style: PresentationStyle = PresentationStyle(),
) -> str:
    """Render structured blocks without frames or markup interpretation."""
    output = StringIO()
    console = Console(
        file=output,
        color_system="standard" if style.color else None,
        force_terminal=style.color,
        force_interactive=False,
        height=25,
        legacy_windows=False,
        no_color=not style.color,
        width=style.width,
        _environ={},
    )
    for index, block in enumerate(blocks):
        if index:
            console.print()
        console.print(Text(block.heading, style="bold cyan"))
        for line in block.lines:
            console.print(Text(line.text), soft_wrap=not line.wrap)
    return output.getvalue().rstrip("\n")
