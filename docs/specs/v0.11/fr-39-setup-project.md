# FR-39 — `setup-project`

Status: Accepted by Moofon (2026-08-15)

Version: v0.11

Phase: 2 (shared with FR-43, which has its own spec and its own acceptance set)

Governing decisions: **ADR-026** (as amended 2026-08-15) governs the delivery
shape; ADR-014 (overlay lifecycle), ADR-015 (Canonical Content and Pointer
Stubs), ADR-016 (language), ADR-021 (process), ADR-022 (configuration, not
application source), ADR-023 (upstream facts under a drift guard), and ADR-024
(Engineering Flow spine) are binding. ADR-025 is accepted but targets v0.12 and
nothing here implements it. The module boundaries in `docs/architecture.md` bind
where terminal policy and manifest reads may live.

---

## Problem Statement

**A generated project hands the user a configuration file and no way through
it.** The upstream template's `.env` carries values a user must decide —
the superuser email, whether email sending works, whether errors are reported —
alongside values dev-ready already generated for them. v0.10 (FR-38) fixed the
worst of the silence: `.env` is now git-ignored, and both the generation report
and the generated `README.md` disclose that a superuser login exists and where
its password lives. But disclosure is not configuration. The user is told the
login exists; they are still left to open `.env`, work out which of its keys are
theirs to change, and edit it by hand.

**The one value most worth changing is also the one with a timing trap.** The
generated backend creates the superuser on first start and looks it up by email.
Editing the password afterwards changes the file and not the login, and raises
no error. FR-38 recorded this fact honestly — the generation report prints it —
but the same report's second step tells the user to start the project. A user
following the printed order walks into the trap before anything has offered to
help them avoid it. The sequence was correct in v0.10, when no setup step
existed to run first; it becomes wrong the moment one does.

**Nothing names a run-once setup step at all.** The generated Flow Chain begins
at `grill-with-docs`, which is a step for building a feature, not for
configuring a project that has never been run. The flow already vendors a
configuration skill — `setup-matt-pocock-skills`, which seeds the issue-tracker,
triage-label, and domain-document conventions — and no generated document
mentions it, so it is installed and invisible.

**Configuration is not a one-shot event, and nothing supports returning to it.**
A user who declines email at generation time has no way back in short of reading
`.env` and upstream's `deployment.md`. A user who wants to change the superuser
email months later, after the project has been started, faces the trap above
with no guidance on which routes exist or what each one costs.

**A user who has started their project needs different advice from one who has
not**, and no generated document distinguishes them. The advice that is correct
before first start ("set these two values, then start") is actively wrong after
it, and the correction is not obvious: the superuser fields cannot simply be
deleted, because the generated settings require them; and deleting the superuser
row does not stick, because the start-up script re-runs the initializer on every
start.

## Solution

A new dev-ready-original skill, **`setup-project`**, written into every
generated project and named as the first entry of every [[Flow Chain]]. It is
the project's [[Setup Step]]: the run-once configuration a project needs before
any other step, and the place a user returns to when one part of that
configuration changes.

It **explains and stops.** It reads the project's current state, reports it,
asks only about the sections the user picks, writes the values they give, and
never runs a command that could destroy data. Where a change is destructive, it
names the routes and their costs and lets the user choose and run one.

Its shape is **section-based and re-runnable**, and a first run is the same
procedure as a fifth run with nothing yet set — so there is one procedure to
maintain and one to learn, not a wizard plus a repair mode. Three sections are
shared by every project because they configure the base template: the superuser,
email sending, and error reporting. The selected [[Engineering Flow]]
contributes its own sections on top; for `mattpocock` that is the issue-tracker
configuration, which hands off to the vendored `setup-matt-pocock-skills` when
the user wants it changed.

The **superuser section alone** is gated on whether the project has already been
started, because that is the only section whose change is expensive after first
start. Email and error reporting take effect on a restart and destroy nothing,
so neither carries a warning — a warning printed on every section would train
the user to skip all of them.

The **generation report's next steps** name `setup-project` before the first
start, so the printed order stops leading the user into the trap the same report
discloses.

## User Stories

1. As a developer who has just generated a project, I want the printed next
   steps to tell me to configure it before I start it, so that I do not create a
   superuser I then have to migrate away from.
2. As a developer who has just generated a project, I want one named place to go
   for setup, so that I do not have to work out which of `.env`'s keys are mine
   to decide.
3. As a developer, I want the setup step to be discoverable by the coding agent
   I actually use, so that asking my agent to "set up this project" finds it.
4. As a developer using an agent other than Claude Code, I want the setup step
   present at my agent's own skills directory, so that dev-ready's support for
   my agent is not silently partial for the one step that comes first.
5. As a developer, I want to be asked for my superuser email, so that my login
   is an address I own rather than a template default.
6. As a developer, I want keeping the generated random superuser password to be
   the default answer, so that the secure choice is the one I get by pressing
   Enter.
7. As a developer, I want to be told that the superuser is created on first
   start and looked up by email, so that I understand why the order of these
   steps matters.
8. As a developer who does not need email sending yet, I want one question that
   lets me decline both email and error reporting, so that a setup I do not need
   costs me one keystroke.
9. As a developer who does need email sending, I want to be asked for exactly
   the values my provider gave me, so that I am not asked to invent settings I
   have no basis for choosing.
10. As a developer on a provider that requires an implicit-TLS port, I want to
    be told which single value to change and where, so that an unusual provider
    is a one-line edit rather than a dead end.
11. As a developer, I want to be told that an app password is safer than my
    account password, so that I do not hand my mail account to a container.
12. As a developer, I want to be told before I type my mail password that what I
    type enters this conversation and its stored transcript, so that I can
    decide whether to type it or paste it into the configuration file myself.
13. As a privacy-conscious developer, I want the option to leave the password
    blank and set it by hand, so that declining does not cost me the rest of the
    interview.
14. As a developer, I want to be told that the configuration file is ignored by
    git, so that I know the values I just entered will not be committed.
15. As a developer, I want the values dev-ready generated for me shown rather
    than asked for, so that I am not invited to replace a strong random secret
    with something I made up.
16. As a developer, I want never to be asked for the deployment domain during
    setup, so that I do not break my own local project by answering a question
    whose only correct local answer was already filled in.
17. As a developer preparing to deploy, I want to be pointed at the upstream
    deployment document, so that I know the deployment-time values exist and
    where they are explained.
18. As a developer returning months later, I want the setup step to report what
    is currently configured, so that I can see the project's state without
    reading the configuration file.
19. As a developer returning months later, I want to configure email alone
    without being walked through every other section, so that a small change
    costs a small amount of my time.
20. As a developer who has never run the project, I want the superuser section
    to write the values and stop, so that setup before first start is
    uneventful.
21. As a developer who has started and then stopped the project, I want to be
    recognised as having started it, so that I am warned even though nothing is
    currently running.
22. As a developer who has started the project, I want to be shown both a reset
    route and a route that keeps my data, so that "I already have data" is not
    treated as an error.
23. As a developer, I want the destructive route to be described and not
    executed, so that no skill deletes my database on my behalf.
24. As a developer, I want the data-keeping route spelled out step by step, so
    that the safer option is not also the vaguer one.
25. As a developer changing email settings on a running project, I want no
    data-loss warning, so that warnings keep meaning something when they appear.
26. As a developer on a machine without Docker, I want to be asked one question
    rather than have my project's state guessed at, so that a wrong guess does
    not decide whether I am warned.
27. As a developer on the `mattpocock` flow, I want to be told what my issue
    tracker is currently configured as, so that I know the convention exists
    before I write my first spec.
28. As a developer on the `mattpocock` flow, I want the setup step to hand off
    to the flow's own configuration skill only when I want the configuration
    changed, so that a step I do not need is not run at me.
29. As a developer, I want to be told that changing those files makes them
    mine, so that I understand why later upgrades stop updating them.
30. As a developer, I want the setup step to be one I invoke, so that an agent
    does not decide on its own to reconfigure my project mid-task.
31. As a developer with a large project, I want the setup step's own file to
    stay small, so that having it at the head of every chain does not consume
    the context I need for my actual work.
32. As a maintainer, I want adding the next Engineering Flow to require filling
    in one table entry rather than copying an interview, so that the setup step
    does not fork once per flow.
33. As a maintainer, I want the base-template facts this skill states to fail a
    test when upstream changes them, so that a pinned-commit bump cannot quietly
    turn generated guidance into a lie.
34. As a user of an existing v0.10 project, I want the setup step to arrive on
    upgrade, so that the feature is not restricted to projects generated after
    it shipped.

## Implementation Decisions

### Delivery shape

- **`setup-project` is written unconditionally.** It is not a [[Catalog Item]],
  it is in no [[Engineering Flow]]'s `paths`, and it is in no flow's `steps`. It
  is not declared in the manifest's vendored section, so the FR-16 byte-equality
  drift guard's covered-path set is unchanged.
- **It joins the overlay content mapping before the Pointer Stub projection.**
  This is the load-bearing ordering constraint (ADR-026 as amended). The
  projection builds one [[Pointer Stub]] per skill-capable [[Agent Target]] by
  scanning already-collected content for canonical `SKILL.md` paths; the
  unconditional documentation scaffold is consumed *after* it. Delivering
  `setup-project` through the scaffold path would write [[Canonical Content]]
  and no stub at all, leaving the chain's first entry the only one no agent can
  discover. Stating this as an ordering rule rather than as a stub count is
  deliberate: v0.12's Skill Delivery Mode builds `symlink` and `copy` from the
  same step and the same collected set, so a `setup-project` added after it
  would be missed by every mechanism and by that migration.
- **Its source lives under a new root for dev-ready-original skills**,
  `templates/skills/`. The vendored snapshot root is where the maintainer sync
  tool materializes manifest-declared files and has no orphan detection, so an
  original skill placed among them would fail nothing while being
  indistinguishable from content that must never be hand-edited. The flow's own
  original-content root is ruled out by this skill not belonging to a flow. The
  new root makes the distinction structural — everything under the vendored root
  is vendored without exception — and v0.12's second flow inherits the answer.
- **The skill's entry file is a template**, because its flow-dependent paragraph
  is a template token filled from the selected flow id at generation time. Token
  expansion applies only to template-suffixed sources, and the renderer rejects
  any double brace surviving expansion, so **the authored text may contain no
  literal `{{` or `}}`** — a real constraint for a document that discusses
  Compose and reverse-proxy configuration.
- **It declares `disable-model-invocation: true`**, matching every other chain
  entry, so the generated rules file's claim that the chain's steps are
  user-invoked stays true for the first step too.
- **The entry file is a router.** The migrate procedure and the email walk live
  in separate files inside the skill folder — the pattern the vendored
  configuration skill already uses for its issue-tracker seeds. Context bloat is
  this project's first-listed risk and this file sits at the head of every chain.

### Per-flow content

- **Per-flow prose lives in one table keyed by flow id**, inside the overlay
  rendering module, holding this skill's hand-off paragraph and (per FR-43) the
  chain guidance. A selected flow with no entry raises an overlay error rather
  than rendering an empty section. FR-39 owns the table's structure; FR-43 owns
  the chain-guidance column's content.
- **The whole issue-tracker section is per-flow, not shared.** The tracker,
  domain, and triage-label documents all arrive on the `mattpocock` flow's own
  original-content path, and the vendored configuration skill is one of that
  flow's steps. A shared section reading those files would, from v0.12, read
  files another flow never wrote and offer a skill it never installed. The state
  read moves into the table entry alongside the delegation. An existence check
  in the shared section was rejected: it keeps flow knowledge in shared code
  behind a conditional, and each new flow re-opens the question.
- **The shared interview therefore covers exactly three sections** — superuser,
  email, error reporting — and the section menu is those three plus whatever the
  selected flow contributes. The menu is not a fixed list, and this is accepted.

### What the interview asks, and what it refuses to ask

- **Asked:** the superuser email; the superuser password, with "keep the
  generated random value" as the default; then one gate for email and error
  reporting, defaulting to no. On yes it asks exactly five values: the SMTP
  host, user, and password, the from-address, and the error-reporting DSN.
- **Left at upstream's defaults:** the SMTP port, TLS, and SSL flags. The skill
  names them as a single edit for a provider requiring implicit TLS rather than
  asking three questions almost every user answers identically.
- **Displayed, never asked for:** the application secret key and the database
  password. Both are per-project random values dev-ready generated; inviting a
  user to replace them lowers security.
- **Never asked for:** the deployment domain, the frontend host, the CORS
  origins, the environment name, and the container image variables. At setup
  time the only correct local value of the domain is the loopback host, and it
  is interpolated into both the reverse-proxy routing rules and a build argument
  baked into the frontend bundle, so any other value breaks the project on day
  one. The image variables are absent from the configuration file at the pinned
  commit and belong to deployment. The skill closes by pointing at upstream's
  deployment document for all of them.
- **Secret hygiene.** The skill states that the configuration file is
  git-ignored and that a provider app password is safer than an account
  password, and it never echoes a secret back to the terminal. The SMTP password
  additionally **discloses its input cost before asking**: what the user types
  enters the conversation and its stored transcript — a different system with a
  different retention policy from the project's own disk — and the same line
  offers leaving it blank and setting it by hand. It is the only asked value
  with this exposure; the superuser password defaults to keeping a generated
  value so nothing is typed, and an error-reporting DSN is shipped in client
  bundles by design. Not asking for it was rejected: that pushes the hardest
  field back to hand-editing, which is what this requirement exists to remove.
  The boundary is drawn at the transcript and **not** at the agent — an agent
  that can read the configuration file already sees the secret key, the database
  password, and the superuser password, so "keep it from the agent" is a line
  this skill cannot hold.

### The started-project branch

- **It gates the superuser section only.** Email and error-reporting changes
  need a restart and destroy nothing, so those sections carry no warning.
- **Two measured facts make the naive advice wrong**, both read at the pinned
  commit: the superuser email and password are required settings with no
  defaults, so neither can be deleted without breaking start-up; and the
  start-up script runs the database initializer on every start, with the backend
  waiting on its successful completion, so a superuser row deleted by hand
  returns on the next start.
- **Detection reads Docker's own Compose project label** rather than upstream's
  volume name. This incurs no ADR-023 drift-guard debt and survives an upstream
  rename. Listing containers is insufficient, because a plain stop keeps the
  volume — the durable evidence is the volume, not a running container. A
  positive result is conclusive; a negative result is not (a renamed project
  directory or an overridden project name both defeat the label match), so a
  negative result is confirmed with the user rather than acted on as fact.
- **When Docker is absent the skill asks one question** instead of guessing.
- **It offers two routes and runs neither.** Reset destroys data by removing the
  volumes. Migrate keeps it: create the new superuser inside the running
  application, repoint the configured email, delete the old row, and rotate the
  configured password to a fresh unused value.

### Report and lifecycle

- **The generation report's next steps name `setup-project` before the first
  start.** The step is unconditional because the skill is, it states why it
  comes first, and the report stays plain text with no colour — the report is a
  pure rendering function and terminal policy stays in the CLI layer, exactly as
  FR-44 settled in Phase 1. Relying on the generated rules file alone was
  rejected: that file addresses the agent, and the person reading the terminal
  after generation is the one choosing whether to start the project.
- **`setup-project` becomes a managed path in the stamp inventory**, so a v0.10
  project receives it as an added file on upgrade, and a user who edits it is
  preserved and reported under the existing ADR-014 rules. Moving it into a
  flow's paths later would retire a managed path under the obsolete-file rules;
  that reversal cost is accepted.
- **The stamp stays at version 5.** Nothing here adds, removes, or re-types a
  recorded field.

## Testing Decisions

A good test here asserts what a generated project *contains* and what the user
is *shown*, not how the overlay assembled it. Every assertion below is made
against rendered output through an existing seam; no test reaches into the
per-flow table, the private guidance helper, or the projection internals.

**Four seams, three of them already load-bearing.**

1. **The overlay content builder / `apply_overlay`** — a pure function from a
   resolved selection to a path-to-bytes mapping, already carrying the bulk of
   the overlay suite. Everything about presence, absence, and reach is asserted
   here:
   - `setup-project` present as Canonical Content under every selection,
     including the empty selection — the existing "everything / nothing / mixed"
     parametrization is the prior art and the shape to reuse.
   - **A Pointer Stub for it at every selected Agent Target's skills directory**,
     asserted for a multi-target selection and carrying the canonical
     frontmatter. Prior art: the existing stub-content and single-target stub
     tests. This is the assertion that would have caught the delivery defect;
     "present in every generated project" passes on the canonical file alone.
   - A selection with no Agent Targets still writes the canonical file and no
     stubs.
   - A selected flow absent from the per-flow table raises an overlay error,
     asserted through a synthetic catalog at the same seam rather than by
     calling the table.
2. **The report renderer** — a pure function, already covered by an ordering
   test and a plain-text test. Added: the next-steps block names `setup-project`
   at a lower index than the first-start command, asserted on both a minimal
   selection and a whole-catalog selection, with the existing plainness
   assertion extended to cover the new line.
3. **The manifest loader** — asserts `setup-project` appears in no flow's steps
   and in no vendored path, and that the vendored configuration skill is still a
   declared step of `mattpocock`, which is what keeps this skill's prose
   cross-reference honest.
4. **A new offline frontmatter guard** (ADR-023). Reading the committed
   snapshots, it asserts that the chain's vendored entries and the vendored
   configuration skill still declare `disable-model-invocation: true`, and that
   `setup-project`'s own source declares it. This is the only new seam: nothing
   currently asserts anything about template *content*. It is a unit test rather
   than a CI script so that an upstream bump changing that posture fails the
   test suite rather than shipping a generated rules file that lies.

All tests are unit tests, use `tmp_path`, and make no network call. The vendored
drift check and the notices sync check must pass untouched.

**What no test can assert.** The interview itself — that it asks the right
things in the right order, that its warnings land where they should, that the
started-project routes read clearly — is prose, and no CI job can check it. Its
coverage is the by-hand verification in Phase 5 against two generated projects,
one never started and one started and then stopped. That is a stated limit of
this spec, not an omission from it.

## Out of Scope

- **Running any destructive command.** The skill describes the reset and migrate
  routes and executes neither, in any circumstance.
- **Skill Delivery Mode (ADR-025 / FR-46).** Pointer Stubs remain the delivery
  mechanism for all of v0.11. Nothing here creates a symbolic link, a junction,
  or a per-agent content copy.
- **The second Engineering Flow.** `superpowers` ships in v0.12 and supplies its
  own table entry then. This spec only guarantees the table makes that a
  fixed-size change.
- **Editing upstream application source.** The skill configures; ADR-022 stands.
- **Deployment-time configuration.** The domain, hosts, CORS origins,
  environment, and image variables are named as out of scope inside the skill
  itself and delegated to upstream's deployment document.
- **Claude Code Output Styles.** Raised and deferred in the Phase 2 grilling
  session, recorded as D-4 in `docs/catalog-candidates.md`, to be decided
  alongside FR-46. No ticket here touches it.
- **README work.** Both English READMEs and the Chinese overview are Phase 5's,
  in one pass over settled text.
- **A stamp version bump.** Version 5 stands for the whole of v0.11.
- **Any change to the drift guard's covered-path set.**

## Further Notes

**This is dev-ready's first unconditionally-written skill.** The two nearest
existing tests — for a retired handoff protocol and a retired orientation skill —
are both *negative*, asserting that skills are no longer written. Nothing in the
codebase yet writes a skill outside catalog selection, which is precisely why
the delivery defect this spec corrects was available to be made: the
unconditional path that existed was built for documents, and documents need no
projection.

**The per-flow table is the property being bought.** Adding a flow in v0.12
becomes a fixed checklist — a manifest entry, its vendored paths, one table
entry, one flow explainer document — rather than a fork of an interview that is
about the FastAPI template and not about the flow. Three of this skill's four
parts are base-template configuration; only the hand-off and the tracker section
vary. That ratio is the whole argument for ADR-026, and the second grilling pass
corrected the count from one flow-dependent part to two.

**Warning discipline is a design position, not a detail.** A data-loss warning
appears in the superuser section and nowhere else. Printing one at the top of
every run, or on every section, is the cheaper implementation and the worse
product: a warning the user meets on sections that destroy nothing is a warning
they learn to dismiss on the one section that does.
