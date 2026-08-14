# FR-44 — CLI Presentation

Status: Accepted by Moofon (2026-08-13); amendment accepted 2026-08-14

**Amendment 2026-08-14 — the report names the stamp's inventory, not `check`.**
As accepted, this spec said the report names "the read-only inspection command"
as the way to see the full file list, while its own Out of Scope forbade changing
what that command reports. `dev-ready check` renders a drift verdict and has
never printed the managed-file paths, so the two statements could not both hold.
The Out of Scope boundary is kept and the naming sentence is corrected: the
report points at the `inventory` entries in `.dev-ready.json`, which every part
of this spec already calls the authoritative list. A command that prints the
inventory is a capability this version does not have; it is recorded below as a
candidate for a later requirement rather than added inside a presentation phase.

Version: v0.11

Phase: 1 (shared with FR-42, which has its own spec and its own acceptance set)

Governing decisions: ADR-004, ADR-011, ADR-016, ADR-021, ADR-024 (as amended
2026-08-13); the module boundary and dependency rules in `docs/architecture.md`
are binding on where terminal policy may live

## Problem Statement

**The prompts look like nothing.** dev-ready's interactive screens use its
prompt library's stock appearance — no consistent marker, no consistent
highlight, no visual distinction between a question, an answer, and an
explanation. Beside the Node-ecosystem installers a user has already met, the
tool reads as unfinished, and first impressions of a scaffolding tool are formed
entirely on the one screen it shows. This was originally raised as an argument
for changing how dev-ready is distributed; that argument was rejected and this
one survived it, because the polish belongs to the prompt library, not to the
launcher.

**The success report ends in a wall of text.** The report lists every file it
wrote by joining every path with commas onto a single line. Measured on the
current release: **2,398 characters on one line for the leanest possible
project**, and **39,089 characters for a whole-catalog selection with every
Agent Target** — 989 paths. The line wraps across a terminal as an
undifferentiated block, and it buries the four things immediately after it that
a user actually needs: where the project is, what to run next, and the login and
password location the previous version added precisely so a user would not have
to go looking. The one measurement that matters most is the leanest case,
because it is the default path: a user who accepts every default is the user
most likely to be new, and they receive the wall too.

Both numbers grow within this same version. The next phase vendors over a
hundred additional design documents.

**An announced flow needs a visual treatment, not only a behavioural one.**
The selection work makes an unreleased flow unselectable. Nothing yet says what
it should *look* like, and a row that the cursor silently refuses to land on,
with no visual explanation, reads as a bug rather than as a promise.

## Solution

Every prompt is drawn from one style definition, so the marker, the pointer, the
highlight, the selected answer, and the instruction text are consistent from the
first question to the last. An announced flow is drawn as a dimmed row carrying
its own short explanation, so a user who cannot select it can see why. Nothing
is added to the dependency list to achieve this: the prompt library already in
use accepts a style definition and already supports an unselectable choice.

The success report is re-laid-out around what a user does next. The file list
becomes a count with a short breakdown rather than a transcript, and the recorded
inventory in `.dev-ready.json` is named as the way to see the full list. The
location, the next steps, and the credential disclosure keep their place and stop
being pushed below a block of paths.

The report stays plain text and gains no colour. It is produced by a pure
function, and terminal policy belongs to the command-line layer; colouring the
report would mean threading a decision — is this a terminal, and has the user
asked for no colour — down through a module that is currently free of that
concern, creating a permanent policy surface to maintain and test. The prompts
are where colour pays, and the prompts only ever run on a terminal.

## User Stories

1. As a first-time user, I want the prompts to look deliberate and consistent, so that the tool reads as finished rather than as a script someone wired up.
2. As a user, I want the same visual marker on every question, so that I can tell at a glance what is being asked of me.
3. As a user, I want a clear visual difference between the row I am on and the rows I am not, so that I never select the wrong item by miscounting.
4. As a user, I want an instruction line telling me how to answer a multi-select, so that I do not have to guess which key toggles and which key submits.
5. As a user facing a long Category list, I want to know I can type to filter it, so that a hundred entries is a list I can navigate rather than one I must scroll.
6. As a user, I want an unreleased flow drawn as dimmed with a short explanation, so that a row I cannot select looks intentional rather than broken.
7. As a user, I want the answers I have already given to remain visible as I move through the questions, so that I can see what I have chosen without starting over.
8. As a user who just generated a project, I want to see how many files were written rather than all of their names, so that the report tells me the outcome instead of reciting it.
9. As a user, I want a short breakdown of what those files are, so that the count means something.
10. As a user, I want to be told how to see the full file list, so that nothing is hidden from me — only summarised.
11. As a user, I want the project location and the next steps visible without scrolling back, so that the first thing I need is the first thing I see.
12. As a first-time user, I want the first-login details to stay prominent, so that the disclosure the previous version added is not buried by a longer report.
13. As a user selecting the whole catalog, I want a report of the same shape as a default user's, so that asking for more does not degrade the output.
14. As a user piping the output to a file or a pager, I want plain text with no escape sequences, so that what I capture is what I saw.
15. As a user in a terminal with no colour, I want every prompt still fully legible, so that styling never carries meaning that colour alone conveys.
16. As a continuous-integration pipeline, I want the staged progress lines to keep degrading to plain lines with no spinner and no escape sequences, so that build logs stay readable.
17. As a maintainer, I want the style defined in one place, so that a new prompt is styled by existing.
18. As a maintainer, I want no new runtime dependency for any of this, so that the install surface does not grow for appearance.
19. As a maintainer, I want terminal policy to stay in the command-line layer, so that the module boundaries the architecture document states remain true.
20. As a maintainer, I want the report to stay a pure function of its arguments, so that it remains testable without a filesystem or a terminal.

## Implementation Decisions

**One style definition, applied at the terminal implementation.** The prompt
library's style object is constructed once and passed to every prompt. It is
constructed inside the only module permitted to import that library, so no other
module gains a dependency on it and the injectable prompt seam is unchanged in
shape.

**The announced-flow row is dimmed and carries an explanation.** The
unselectable-choice capability itself is specified in FR-42, because it is a
selection-behaviour requirement; what belongs here is its appearance — dimmed,
with a short reason rendered beside it, and no version number in that text.

**A long list gets an instruction line.** The multi-select prompts already
enable prefix filtering; nothing tells the user so. The instruction text says
it. This matters most for the Design Category, which the next phase enlarges by
two orders of magnitude, and it is cheaper to state it now than to discover it
then.

**The report's file list becomes a count with a breakdown.** The report names
how many overlay files were written and groups them, and names the `inventory`
entries in `.dev-ready.json` as the way to see every path. This is a presentation
change only: nothing changes about which files are written or about the recorded
inventory, which remains the authoritative list.

**The report points at the inventory rather than at `dev-ready check`.**
(Amended 2026-08-14.) `check` answers a different question: it renders a drift
verdict against the stamp and the manifest, it prints no paths, and it exits 7
when it finds drift. Naming it here would promise output it does not produce, and
would tie "show me what you wrote" to a policy result. The stamp is in the
project the user was just told to `cd` into, it holds one entry per managed file,
and this spec already treats it as authoritative. Giving `check` an inventory
mode is a defensible product change, but it is a new capability on a lifecycle
command, and this requirement is presentation.

**The report gains no colour, and this is a boundary decision rather than a
taste one.** The report renderer is a pure function of its arguments — that is
what makes it testable without touching a filesystem or a terminal — and the
architecture document places terminal policy in the command-line layer.
Colouring it would require deciding, at print time, whether output is a terminal
and whether the user has asked for no colour, then threading that decision into
the renderer. That is a permanent policy surface, and the value bought is small
next to the prompts, which run only on a terminal and are where the original
complaint was made.

**The existing progress rendering is preserved exactly.** Staged status lines on
the error stream, a spinner on a terminal and plain lines without one otherwise,
no fabricated percentages. This is a regression boundary, not a nicety: it is
the one part of the presentation that already degrades correctly, and it is
asserted as such.

**No new runtime dependency.** The prompt library already present supports
everything above. A richer terminal library is not added.

## Testing Decisions

A good test here asserts what is observable in captured output — the bytes of
the report, the presence or absence of escape sequences, and the arguments a
prompt was constructed with. **Appearance itself is not assertable**, and this
spec says so rather than implying coverage it does not have: the style is
applied inside the module that speaks to the terminal, below the injectable
seam, and rendering it requires a real terminal. What can be asserted is stated
below; what cannot is verified by hand in the documentation and release phase,
which is where that verification is recorded.

No new seam is introduced.

**The report** is tested through the report-rendering function directly, which
is pure and already tested that way. Prior art: the existing report tests assert
the rendered string for several selections. New coverage asserts that the file
list is a count and a breakdown rather than a path transcript; that the recorded
inventory is named as the way to see the full list, and that `dev-ready check` is
not named as that way; that the location,
next steps, and credential disclosure are present and ordered; that the rendered
string contains **no escape sequences for any selection**, including the
whole-catalog one; and that the whole-catalog report has the same shape as the
default one rather than a degraded version of it.

**The unselectable row's presentation** is tested through the injected asker at
the answer-collection seam, asserting that the announced flows are passed as
unselectable together with their explanatory text and that the text names no
version. The behavioural half of this — that the resulting selection can never
be an announced flow — belongs to FR-42's coverage.

**Progress rendering** is tested through the existing progress renderer with its
terminal flag forced off, asserting plain lines and no escape sequences, and
with it forced on, asserting the spinner starts and is cleared. Prior art: these
tests exist and are a regression boundary here rather than new coverage.

**Absence of a new dependency** is asserted by the project's dependency
declaration remaining unchanged; the lock file refresh in the release phase is
where a violation would surface loudly.

**Manual verification** is recorded, not automated: running the interview on a
real terminal to confirm the styling is applied, the announced rows are dimmed
and unreachable, and the instruction line appears on the long Category list.
This is stated as a step in the documentation and release phase, alongside the
plugin-manifest installation check, because it is the same kind of check — one
no continuous-integration job can make.

## Out of Scope

- Colouring the success report, the progress lines, or any error message, and
  therefore any terminal detection or no-colour convention. If report colour is
  ever wanted, it arrives with the policy surface it needs, deliberately.
- Any new runtime dependency, and specifically a richer terminal library.
- Changing which files are written, how the inventory is recorded, or what the
  read-only inspection command reports. The report's file list becomes a
  summary of the same set. This boundary is what the 2026-08-14 amendment keeps:
  `dev-ready check` gains no managed-file output, in text or in JSON, and its
  exit codes are unchanged.
- Any new command or flag that prints the managed-file list. The report names the
  recorded inventory instead. See Further Notes for the follow-up this leaves.
- Changing the staged progress model: the stages, their order, the error stream
  they are written to, and the absence of a percentage all stay as they are.
- The selection behaviour of an announced flow, the prompt sequence itself, and
  every flag. All belong to FR-42; this spec styles what that one decides.
- Localizing any of it. Everything emitted stays English; there is no message
  catalog, no language flag, and no locale detection.
- A terminal user interface, a progress bar with a fraction, or any interactive
  screen beyond the prompts that already exist.

## Further Notes

This requirement's scope is narrower than its title, deliberately. It entered
the roadmap attached to a rejected proposal about distribution, and the surviving
half was specifically about the **prompt screens**. Reading it as "make the CLI
look good" would pull in report colour, and report colour is the one part that
costs a permanent policy surface rather than a style definition.

The report measurement is the part of this that is not a matter of taste. A
2,398-character single line on the default path is a defect by any reading, and
it has been shipping since the report learned to list overlay paths. It is
grouped here because the same phase is already editing presentation, not because
it is presentational in the same sense as the prompt styling.

The 2026-08-14 amendment leaves one follow-up, stated here so it is not lost: a
user who wants the managed-file list must open a JSON file and read one field.
That is honest and it is zero risk, but it is not a good answer for a first-time
user. The good answer is a command that prints the inventory. It does not belong
to `check`, whose verdict and exit codes serve a different question, and it does
not belong to a presentation requirement. It is a candidate for a later version,
and it needs its own grilling: what it prints, whether it filters, and whether it
reads the stamp or the project.

The honest gap is that the styling itself has no automated assertion. That is a
property of where the style must be applied — the module that owns the terminal
— and not a gap this spec could close by moving code, because moving the style
above that boundary would put terminal concerns into modules the architecture
document forbids them in. The manual check in the release phase is the coverage,
and naming it here is what keeps it from being forgotten.
