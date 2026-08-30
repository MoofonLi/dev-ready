# Recorded Capture of a real interactive `dev-ready init`.
# Replay from the repository root: `vhs docs/assets/demo.tape`
# Native VHS needs `ttyd`, `ffmpeg`, `git`, and `dev-ready` on PATH.
# The image is this tape's output; do not draw or screenshot a replacement.

Output docs/assets/demo.gif

Require git
Require dev-ready

Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 760
Set Padding 8
Set Framerate 8
Set PlaybackSpeed 2
Set TypingSpeed 25ms
Set CursorBlink false
Set Theme "Catppuccin Mocha"
Set WaitTimeout 180s

Hide
Type "rm -rf /tmp/demo && clear"
Enter
Sleep 400ms
Show

Type "dev-ready init demo --dir /tmp/demo"
Enter

# Engineering Flow comparison + select
Wait+Screen@30s /Select an Engineering Flow/
Sleep 1.6s
Down@300ms 2
Sleep 900ms
Up@300ms 2
Sleep 600ms
Enter

# Category prompts (Default Set: no optional Enhancements)
Wait+Screen@15s /Select Security items/
Sleep 700ms
Enter
Wait+Screen@15s /Select Quality items/
Sleep 700ms
Enter
Wait+Screen@15s /Select Design items/
Sleep 900ms
Enter
Wait+Screen@15s /Select Token Optimize items/
Sleep 700ms
Enter

# Agent Targets (claude is the default)
Wait+Screen@15s /Select Agent Targets/
Sleep 900ms
Enter

# Confirmation Static Screen
Wait+Screen@15s /Ready to generate/
Sleep 1.8s
Enter

# Fetch is the long stage; overlay/verify/finalize complete in milliseconds
# and their done-lines stay on screen with the report.
Wait+Screen@180s /Fetching base template/
Sleep 1s
Wait+Screen@180s /project generated/
Sleep 2s

# The tape removes the project it generated.
Hide
Type "rm -rf /tmp/demo"
Enter
Sleep 400ms
