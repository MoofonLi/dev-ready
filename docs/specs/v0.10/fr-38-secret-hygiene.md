# FR-38 — Secret Hygiene and Credential Disclosure

Status: Accepted by Moofon (2026-08-04)

Version: v0.10

Phase: 5b

Governing decisions: ADR-002, ADR-005, ADR-006, ADR-014, ADR-016, ADR-018, ADR-022

## Problem Statement

A project generated with the released v0.9.0 hands its owner three secrets, tells
them nothing about any of them, and leaves the file holding them untracked by
any ignore rule. Everything below was found by generating a project and reading
what came out, not by reading the manifest.

**dev-ready writes secrets into a file that git will happily commit.** Generation
produces a per-project random `SECRET_KEY`, `POSTGRES_PASSWORD` and
`FIRST_SUPERUSER_PASSWORD` in `.env`. That is the right thing to do — the
alternative is shipping upstream's `changethis` placeholders. But none of the
three ignore files in the generated tree — the root one, `backend/`'s, or
`frontend/`'s — carries an `.env` pattern. The user's first `git add .` commits
their own database password and application signing key into history, and
history is the one place a secret cannot be quietly withdrawn from. dev-ready
created the hazard: a user who never ran dev-ready would have had `changethis`
in that file and lost nothing by committing it.

**Nothing anywhere tells the user their login exists.** The generation report's
next steps say to change directory, run `docker compose watch`, and read
`AGENTS.md`. The generated `README.md` lists the stack and the commands. Neither
names `FIRST_SUPERUSER`, neither says a superuser is created on first start, and
neither says where its password is. A user follows the three steps, reaches a
login form, and has nothing to type. The password is twenty-two random
characters in a file they have no reason to open.

The order in which they discover this makes it worse. The generated backend's
`init_db` selects the user by email address and creates one only when none
exists. A user who finds `.env`, decides the generated password is unmemorable,
edits `FIRST_SUPERUSER_PASSWORD`, and restarts gets **no error and no new
password** — the row already exists, the create is skipped, and the file now
disagrees with the database. Nothing in the project explains this, and the
failure presents as a broken template.

**Every generated project allows a third party's hostname through CORS.**
`BACKEND_CORS_ORIGINS` ships with `http://localhost.tiangolo.com` in it, a
literal in upstream's own `.env`. It is upstream's local-testing hostname and
has nothing to do with the user's project.

**Two deployment workflows were pruned in error, which made retained
documentation describe files that were not there.** FR-7 has removed
`deploy-production.yml` and `deploy-staging.yml` since v0.2 on the stated
grounds that they reference upstream's own servers and secrets. They do not.
`deploy-production.yml` opens with the comment `Do not deploy in the main
repository, only in user projects` and guards itself with
`github.repository_owner != 'fastapi'` — upstream wrote both for downstream
users, and they are the only two of the ten pruned workflows that were. Because
dev-ready keeps `deployment.md`, and that document spends its Continuous
Deployment sections teaching how to use those two files, every generated project
has carried a deployment guide pointing at machinery dev-ready had deleted. The
documentation was never wrong; the prune list was.

## Solution

dev-ready takes ownership of the root ignore file, says out loud what it created,
stops shipping a stranger's hostname, and gives back the two workflows it should
never have taken.

**The generated project ignores its own secrets.** The root ignore file joins the
prune list and dev-ready writes a replacement carrying upstream's entries plus
`.env` and `.env*`. This is the shape FR-7 and FR-8 already established for
`README.md`: prune removes the upstream file so the overlay's no-overwrite rule
still holds, and the replacement is ordinary [[Overlay Infrastructure]] — written
unconditionally, named by no [[Category]], selectable by nothing.

**The two documentation surfaces a new user actually reads name the login.** The
generation report's next steps and the generated `README.md` both state the
superuser email, where the password is, and the fact that changing that password
after the first start does nothing until the database is reset. The report is
what a user sees at the moment generation finishes; the `README.md` is what they
find when they come back a week later. Both are needed, and the second is what
survives.

**`BACKEND_CORS_ORIGINS` loses the third-party hostname.** `.env` is
configuration, so rewriting it is permitted by ADR-022 — nothing under
`frontend/src/` or `backend/app/` is touched by this spec.

**`deploy-production.yml` and `deploy-staging.yml` come back**, and FR-7's entry
records why they were wrong to remove, so the next audit of the prune list does
not repeat the reasoning that removed them.

## User Stories

1. As a developer generating my first project, I want `.env` ignored by git from
   the moment the project exists, so that my first commit does not publish a
   database password I did not choose.
2. As a developer who has already run `git init && git add .`, I want the ignore
   rule to have been there before I did, because no later fix removes a secret
   from history.
3. As a developer, I want any file matching `.env*` ignored, so that a
   `.env.prod` or `.env.local` I invent later is covered without my remembering
   to add it.
4. As a developer, I want the ignore file to keep everything upstream ignored —
   `node_modules/`, the Playwright output directories, the VS Code exception —
   so that taking dev-ready costs me nothing I had before.
5. As a developer reading the generation report, I want to be told the superuser
   email address, so that I know what to type into the login form.
6. As a developer reading the generation report, I want to be told which key in
   `.env` holds the superuser password, so that I do not have to read a
   twenty-line file to guess.
7. As a developer, I want to be told that changing the superuser password after
   the first start has no effect, so that I do not spend an afternoon concluding
   the template is broken.
8. As a developer who deleted my terminal scrollback, I want the same facts in
   `README.md`, so that the information survives the session it was printed in.
9. As a developer who generated with `--yes` and saw no prompts, I want those
   facts in both places anyway, because I never had a prompt to read them from.
10. As a security-conscious developer, I want `SECRET_KEY` and
    `POSTGRES_PASSWORD` to stay generated rather than become questions, so that
    the values are stronger than ones I would have invented.
11. As a developer, I do not want my project's CORS allowlist to permit a
    hostname belonging to someone else's testing setup.
12. As a developer ready to deploy, I want the deployment workflows
    `deployment.md` describes to actually be in my project, so that the guide I
    was given is executable.
13. As a developer who has not yet set up a self-hosted runner, I want the
    restored workflows to behave exactly as upstream intends, and I accept that
    a release published before that setup leaves a job waiting for a runner.
14. As a maintainer, I want the corrected prune-list reasoning recorded at FR-7,
    so that a future audit does not re-remove the two files.
15. As a maintainer, I want the replacement ignore file's divergence from
    upstream's to be detectable, so that an upstream addition is noticed rather
    than silently dropped.
16. As a maintainer, I want `upgrade` to treat the new ignore file exactly like
    every other managed file — replaced when untouched, preserved and reported
    when edited — with no special case.
17. As a user of an existing v0.9 project, I want `dev-ready upgrade` to tell me
    plainly that my root ignore file is one dev-ready will not touch, so that I
    can adopt the `.env` entries myself, and without it touching the `.env` I
    have since edited. (Corrected 2026-08-05 during implementation — this story
    originally asked for "the ignore file I never had". A v0.9 project *has* a
    root ignore file: upstream's own, unmanaged. See the Implementation
    Decisions note on what upgrade does with it.)
18. As a maintainer, I want no file under `frontend/src/` or `backend/app/`
    to differ from the pinned upstream commit after this work, so that ADR-022
    is observably held.

## Implementation Decisions

**The root ignore file becomes Overlay Infrastructure via prune-and-replace.**
Prune is applied at fetch time — the manifest's `prune` list is merged with
`exclude` and handed to Copier, so a pruned path is never generated at all
rather than generated and deleted. The prune entry is therefore root-anchored,
matching the existing `/README.md` entry, so `backend/` and `frontend/` ignore
files are untouched. The replacement is added to the unconditional writes in the
overlay's content builder alongside the rules file and `README.md`, before any
selection-dependent content.

**The template source file does not itself carry a leading dot.** It is stored
under a `gitignore` template directory with an ordinary filename and mapped to
`.gitignore` at its destination. A real dotfile in the source tree would be
interpreted by git as an ignore rule governing its own directory, and dotfiles
are the class most likely to be dropped by a build backend's default exclusions.
The overlay's single-asset write already takes an explicit destination — that is
how `AGENTS.md.tmpl` becomes `AGENTS.md` — so this costs no new mechanism. The
file needs no template tokens and is written verbatim.

**The replacement's content is upstream's plus two lines.** It carries every
entry the pinned upstream root ignore file carries, then `.env` and `.env*`.
Both are written rather than relying on `.env*` alone: the bare `.env` line is
the one a human scanning the file looks for. Nothing else is added — this is a
correction, not an opinion about what a FastAPI project should ignore.

**Divergence from upstream is detected by comparing against the pinned source,
not inside project verification.** dev-ready now owns a file upstream also
maintains, so an upstream addition no longer arrives automatically. An earlier
draft of this spec said the weekly bump job's regeneration would catch it; that
is wrong, and the reason is worth stating so it is not re-proposed. Pruning is
applied as a Copier exclude at fetch time, so the upstream file is never
generated at all — it is absent from the generated project, and there is
nothing there to compare against. The check therefore resolves the pinned
commit from the manifest, reads upstream's file at that commit, and compares it
against the upstream-derived portion of dev-ready's replacement, failing the
bump PR on any difference. dev-ready's own added entries are excluded from the
comparison by construction. This is the existing vendored-drift mechanism
applied to one more piece of content: network-marked, running in the job the
other real-repository checks already run in, with the comparison logic unit
tested offline against a fixture. No new manifest section and no new runtime
dependency.

**Credential disclosure is constant text in two renderers.** The report renderer
is a pure function of its arguments and stays one — the disclosure is a literal,
never read off disk, so a report can be rendered for paths that were never
written. The `README.md` template gains a section covering the same three facts.
Both name the superuser email as a value dev-ready knows (it is upstream's
`first_superuser` default, unchanged by dev-ready), name the `.env` key rather
than the password itself, and state the first-start ordering rule.

**The disclosed email is guarded against the pin.** (Added 2026-08-05 during
implementation.) The address dev-ready discloses is not dev-ready's to choose —
it is upstream's own `first_superuser` default in `copier.yml`, which
`_template_data` deliberately does not override. It is nonetheless written
literally on two dev-ready-owned surfaces, the report renderer's constant and
the README template, so an upstream change to that default would leave both
telling users to log in as an account that does not exist, with nothing failing.
FR-37's `scripts/check_stack_facts.py` closes it: it already runs against a real
generated project in CI, and the generated `.env` is where the resolved value
lands, so it compares the README's disclosed email against `.env`'s
`FIRST_SUPERUSER` and fails the build on disagreement. An offline test pins the
renderer's constant to the README template, so the two copies cannot drift apart
and holding one to the pin holds both.

**The password is never printed.** The report names the file and the key. A
secret echoed to a terminal lands in scrollback, in CI logs, and in whatever
captured the command's output; the file is already the right place for it and
the user has the file.

**The CORS value is rewritten after Copier runs and before finalization.** The
hostname is a literal inside upstream's `.env`, not a Copier question, so it
cannot be supplied through the answers dev-ready already passes. The rewrite
joins the existing post-Copier staging cleanup that removes Copier's own
metadata — same stage, same all-or-nothing guarantees, still inside staging so a
failure never exposes a partial target. It rewrites only the one key's value and
leaves the rest of the file, including the generated secrets, byte-identical.

**A missing or unrecognisable key is not an error.** If the key is absent, or
the hostname is already gone, the rewrite is a no-op. Generation must not fail
because an upstream default changed shape; the weekly bump job is where that is
noticed.

**`.env` remains outside the overlay's managed inventory.** It is written by
Copier's own tasks, is not in the content builder's output, and is not hashed
into the stamp. The CORS correction therefore applies to newly generated
projects only, and `upgrade` neither rewrites nor reports an existing project's
`.env`. This is correct: `.env` holds the user's live secrets and dev-ready
must not touch them after generation.

**The prune list loses two entries and FR-7 gains an amendment.** The two
deployment workflow filenames are removed from the manifest's prune list, and
FR-7's prose records the measured reason — upstream's own downstream-only guard
— so the original rationale is not re-derived. The other eight pruned workflows
are unaffected.

**No stamp change and no selection surface change.** Nothing here adds a
Category, an item, a flag, or a recorded field. The stamp stays at version 5, as
the v0.10 plan requires. The ignore file enters the managed inventory as an
ordinary path, which is what makes the ADR-014 rules apply to it with no special
case: an untouched file is replaced on `upgrade`, and an edited one is preserved
and reported.

**An existing v0.9 project does not receive the file, and this is the correct
outcome.** (Corrected 2026-08-05 during implementation; this paragraph
originally claimed the opposite.) A v0.9 project already has a root `.gitignore`
— **upstream's own**, written before this change pruned it, and absent from that
project's recorded inventory because dev-ready never wrote it. ADR-014 forbids
replacing a file dev-ready did not write, so `upgrade` reports a conflict the
first time and `Skipped (user-modified)` every time after. The user keeps a file
that does not ignore `.env`, and the report is what tells them so.

Delivering the file to those projects would require recognising upstream's
byte-exact v0.9 copy as unowned-but-replaceable — a special case, and precisely
the kind this spec's own rule refuses. It is therefore **not** in FR-38's scope.
Whether to add such a migration is a separate decision; until it is made, the
mitigation for existing projects is the report line plus the `README.md` text,
both of which name `.env` as the file holding the secrets.

## Testing Decisions

A good test here asserts what a user would see in the generated project, not how
the generator arrived at it. Every assertion below is reachable from an existing
seam; **this spec opens no new seam**, which is deliberate — three of the four
changes are content changes to files that already have tests asserting other
content in the same files.

**Generated content through the overlay's content builder and applier**
(`tests/unit/test_overlay.py` is the prior art). Assert, for a selection that
takes nothing at all: the ignore file is present, it names `.env` and `.env*`,
and it retains upstream's entries; and the `README.md` states the superuser
email, the `.env` key holding the password, and the first-start ordering rule.
Assert also that the ignore file appears in the content inventory, which is what
makes the ADR-014 behaviour follow without being implemented.

**The prune list through the real manifest loader**
(`tests/unit/test_manifest.py` is the prior art). Assert the root ignore path is
present and root-anchored, and that neither deployment workflow filename is.

**Report text through the report renderer by argument**
(`tests/unit/test_report.py` is the prior art). Assert the three facts appear and
that no secret value does — a test that a password is *not* printed is the one
that keeps that property when the renderer is next edited.

**The CORS rewrite through a real generation with a faked snapshot**
(`tests/unit/test_generate.py` is the prior art; it already replaces the fetch
step with a local builder and runs the genuine generation path offline). Extend
that fake to write an `.env` carrying upstream's CORS line and the three
generated secrets, then assert the finished project's `.env` has lost the
third-party hostname, has kept every other allowed origin, and has kept the
secrets byte-identical. Assert the no-op cases separately: an `.env` without the
key, and one where the hostname is already absent, both generate successfully.

**Upgrade behaviour is asserted, not implemented** (`tests/unit/test_upgrade.py`
is the prior art). A v0.9-shaped project without the ignore file receives it; an
untouched one is replaced; an edited one is preserved and reported as divergent.

**The restored workflows are covered by the existing network-marked real
generation job**, which already generates against the true pin and verifies the
result. No unit test asserts the presence of a file that only a real Copier run
produces.

**The upstream-divergence comparison is unit tested offline against a fixture**,
including a fixture where upstream's file has gained an entry and one where it
is missing entirely; the test that reaches the real repository is network-marked
and deselected by default, like every other check that resolves a pinned commit.

Unit tests use `tmp_path`, touch no filesystem outside it, and make no network
calls. The cross-release upgrade gate stays network-marked.

## Out of Scope

- **The generated frontend's footer.** It links to FastAPI's GitHub, X, and
  LinkedIn accounts and captions itself with the template's name. ADR-022
  settles that dev-ready does not edit upstream application source; this spec
  does not revisit it.
- **A `to-prod` deployment skill and an `.env.prod` convention.** Both were
  proposed and rejected on 2026-08-04. Restoring the two workflows repairs the
  defect that justified them, and upstream's `deployment.md` covers the rest.
- **The seven stale `deployment.md` lines** describing `LATEST_CHANGES` and
  `SMOKESHOW_AUTH_KEY`, whose workflows are correctly pruned. Repairing them
  means pruning and rewriting 352 otherwise-accurate lines. Recorded as accepted
  residue in `docs/version-plan.md`.
- **Asking the user for any credential.** That is FR-39's `setup-project` in
  v0.11. This spec discloses what generation already produced; it changes no
  prompt and adds no flag.
- **`SECRET_KEY` and `POSTGRES_PASSWORD` generation.** Unchanged, and
  deliberately so.
- **Rewriting `.env` in an existing project.** `upgrade` does not manage `.env`
  and must not start.
- **The `backend/` and `frontend/` ignore files.** Upstream's are adequate for
  their directories and dev-ready takes ownership of exactly one file.

## Further Notes

The four defects share one cause worth recording: every one of them was found by
generating a project with the released version and reading the output, and none
of them is visible from the manifest, the specs, or the test suite. Two had
survived since v0.2. The v0.10 release phase should generate and read a project
before the version is called done, and so should every release phase after it.

The prune-list error is the more instructive of the two long-lived ones. The
list was audited once, against a real generation, and the audit recorded a
rationale for each entry — but the rationale for these two was asserted rather
than read out of the files, and nothing since re-checked it. The correction is
therefore recorded as prose at FR-7 rather than as a silent list edit: the next
person auditing that list needs the reason the entry is absent more than they
need the entry.
