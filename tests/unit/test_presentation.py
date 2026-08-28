"""Unit tests for the shared Static Screen presentation seam."""

import io
import re

import pytest

from dev_ready.presentation import (
    PresentationStyle,
    ScreenBlock,
    ScreenLine,
    detect_presentation_style,
    render_screen,
)

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


class _TTYBuffer(io.StringIO):
    def isatty(self) -> bool:
        return True


def test_plain_screen_preserves_literal_content_without_ansi() -> None:
    screen = render_screen(
        (
            ScreenBlock(
                heading="Location:",
                lines=(ScreenLine("  /projects/[draft]/my-app", wrap=False),),
            ),
        ),
        style=PresentationStyle(color=False, width=80),
    )

    assert screen == "Location:\n  /projects/[draft]/my-app"
    assert "\x1b" not in screen


def test_non_terminal_stream_resolves_to_plain_fixed_width() -> None:
    stream = io.StringIO()

    style = detect_presentation_style(stream)

    assert style == PresentationStyle(color=False, width=80)


@pytest.mark.parametrize("color", [False, True])
def test_narrow_screen_wraps_prose_but_not_paths_or_commands(
    color: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TERM", "dumb")
    path = "/projects/a-long-directory/my-app"
    command = f"cd {path}"

    screen = render_screen(
        (
            ScreenBlock(
                heading="Next Steps:",
                lines=(
                    ScreenLine(path, wrap=False),
                    ScreenLine(command, wrap=False),
                    ScreenLine("This prose line wraps at the resolved terminal width."),
                ),
            ),
        ),
        style=PresentationStyle(color=color, width=20),
    )

    assert path in screen
    assert command in screen
    assert "This prose line wraps" not in screen
    assert "This prose line \nwraps" in screen


def test_coloured_screen_adds_only_decoration_and_never_a_frame() -> None:
    blocks = (
        ScreenBlock(
            heading="Ready to generate:",
            lines=(ScreenLine("  project name: my-app"),),
        ),
        ScreenBlock(
            heading="Selection:",
            lines=(ScreenLine("  engineering flow: mattpocock"),),
        ),
    )

    plain = render_screen(blocks)
    coloured = render_screen(
        blocks,
        style=PresentationStyle(color=True, width=80),
    )

    assert "\x1b" in coloured
    assert _ANSI_ESCAPE.sub("", coloured) == plain
    assert "project name: my-app\n\nSelection:" in plain
    assert not {"┌", "┐", "└", "┘", "│", "─"}.intersection(coloured)


def test_no_color_disables_colour_for_a_terminal_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NO_COLOR", "1")

    style = detect_presentation_style(_TTYBuffer())

    assert style.color is False
