# herdr-skill+

[![Version](https://img.shields.io/badge/version-0.16.0-blue)](#installation)
[![Type](https://img.shields.io/badge/type-agent%20skill-blueviolet)](#installation)
[![Built with](https://img.shields.io/badge/built%20with-bioinfo--skill--creator-orange)](https://github.com/cheahhl814/bioinfo-skill-creator)

Use when the user mentions Herdr, asks to delegate to another agent, run parallel agents, brainstorm/debate with other agents (cross-examine a design, devil's advocate, second opinion with critique), run sudo (or another privileged/secret-entry command) safely in a managed pane, check another agent's quota/usage, wants a hands-on CLI/bioinformatics tutorial in a side pane while you watch, runs a quiz / knowledge-check (5-6 items, MCQ + spot-the-bug + task) in a side pane, or imports a course from PDF/Markdown/any text source (with LLM-mediated fallback for non-PDF/non-MD). **Workflow-only** — tool schemas (`herdr_layout`, `herdr_pane`, `herdr_agent`) are the source of truth for parameters. Complements the [official herdr skill](https://github.com/herdr).

**Repository**: https://github.com/cheahhl814/herdr-skill-plus

> [!NOTE]
> Current version: **v0.16.0** (updated 2026-09-24). See [Changelog](#changelog) below for what changed.

## Contents

- [Why this skill exists](#why-this-skill-exists)
- [Installation](#installation)
- [Workflow phases](#workflow-phases)
- [Authoring & importing courses](#authoring--importing-courses)
- [Repo layout](#repo-layout)
- [Update check](#update-check)
- [Hard guarantees](#hard-guarantees)
- [Changelog](#changelog)
- [Provenance & License](#provenance--license)

## Why this skill exists

The official herdr skill ships `herdr_layout` / `herdr_pane` / `herdr_agent` tools and their parameter schemas. This skill **does not redefine those tools** — it defines the workflow around them: when to split a pane, when to delegate to another agent, how to gate a prompt on completion, how to recover from stalls, and — since v0.6.0 — how to run a tutoring or quiz session in a human-driven pane without flooding the student with LLM tokens.

If you are looking for the tool API, read `docs-corpus/herdr/` (offline captures of the herdr CLI flags and supported agents). If you are looking for *workflow* (the order in which to call those tools, the checkpoints, the failure recoveries), read `SKILL.md`.

## Installation

This is an **agent skill**, not a user-facing library. There is no `pixi.toml` and no `pixi install` step — the skill is pure Markdown + a single Python importer.

**Option A — give your agent this prompt (recommended):**

```text
Install the herdr-skill+ skill from
https://github.com/cheahhl814/herdr-skill-plus —
clone it into your agent's skills directory (the path your agent watches
for skills). Then read SKILL.md to understand its phases (§1 delegation,
§4.6 provider preflight, §5 sudo pattern, §6 tutorial mode, §7 quiz mode)
and the Input/Output contract for each. Confirm when the environment is
ready.
```

**Option B — manual install:**

```bash
git clone https://github.com/cheahhl814/herdr-skill-plus.git
# Symlink into your agent's skills directory. On Pi:
mkdir -p ~/.pi/agent/skills
ln -sf "$(pwd)/herdr-skill+" ~/.pi/agent/skills/herdr-skill+
```

The skill does **not** install any third-party Python packages at install time. The one tool it ships (`bin/quiz-import-pdf.py`) has optional dependencies — see [Authoring & importing courses](#-authoring--importing-courses).

## Workflow phases

The skill is **not** a phased pipeline (no preflight → run → qc chain). It is a flat workflow library of seven sections; the agent reads the relevant section based on the user's prompt. Each section is **opt-in**: trigger on the matching natural-language request and skip the rest.

| § | Section | When the agent reads it |
|:--|:--------|:------------------------|
| §1 | Delegation sequence (core) | "delegate to claude / codex / opencode / …", "run agents in parallel" |
| §2 | Verification & completion rules | every agent start / prompt — read once, applies forever |
| §3 | Interrupt & error recovery | agent stalls, vanishes, false-settles, blocks |
| §4 | Launch config: model discovery + quota pre-flight | "run agents in parallel" (T2/T3 tasks) |
| §4.5 | Permission / auto-approval modes at launch | delegation to harnesses that block shell commands by default |
| §4.6 | Provider preflight & task-tier matching | T2 / hard-cap / ambiguous-tier tasks |
| §5 | Privileged & secret-entry commands (sudo pattern) | sudo, GPG passphrase, SSH key, 2FA, etc. |
| §6 | CLI / bioinformatics tutorial mode (human-driven pane) | "tutor me on samtools", "teach me this", "run me through chapter 3" |
| §7 | Quiz / knowledge-check mode (human-driven pane) | "quiz me on chapter 3", "test me on …", mixed MCQ + spot-the-bug + task items |
| §8 | Multi-agent brainstorming mode (bidirectional) | "brainstorm with another agent", "debate these two designs", "devil's advocate", "get a second opinion with critique", "have the agents argue it out and converge" |

> [!TIP]
> Every gated decision in §4-§7 surfaces back to the user via `ask_user_question` (Evidence + Recommend + Options) rather than auto-picking. This mirrors how Claude Code and OpenCode surface their permission prompts.

### Natural-language triggers

Trigger phrases (from SKILL.md `triggers:` frontmatter):

```text
- user mentions Herdr by name
- delegate a task to another coding agent
- run agents in parallel / multiple agents at once
- brainstorm / debate / get a second opinion with critique together with other agents (§8)
- cross-examine / stress-test / poke holes in my design or plan using another agent (§8)
- play devil's advocate against my approach (§8)
- get multiple agents to converge on / vote on a design decision (§8)
- run sudo or another privileged command safely
- check another agent's model/quota/usage
- teach/tutor the user on CLI or bioinformatics commands hands-on in a side pane
- run a quiz / knowledge-check in a side pane (MCQ, spot-the-bug, task items)
- import a course from PDF / Markdown into a Markdown spine
- import a course from any text source (YouTube transcript, Notion export, lecture notes)
- author a new course or extend an existing one in the Markdown spine + JSON quiz schema
```

Two new triggers added in v0.6.0 / v0.8.0 / v0.9.0 / v0.10.0 that did not exist at v0.5.0:

- "teach/tutor the user on CLI … hands-on in a side pane" (§6)
- "run a quiz / knowledge-check in a side pane" (§7)
- "import a course from any text source via --llm-stdin" (importer LLM fallback)

New §8 trigger family added in v0.15.0/v0.15.1: brainstorm, debate, second opinion *with critique*, cross-examine, devil's advocate, "argue it out and converge" — these route to the bidirectional brainstorm mode, NOT a one-shot §1 opinion poll (plain "ask another agent X" without a critique/exchange signal still routes to plain §1 delegation).

## Authoring & importing courses

§6 (tutorial mode) and §7 (quiz mode) consume **Markdown** as the spine. JSON is reserved for the lesson→quiz boundary. The skill ships one CLI to scaffold this layout from arbitrary sources.

### Course layout (produced by the importer, or hand-authored)

```
course-materials/
├── README.md                     # top-level course map (mermaid)
└── <lesson-slug>/
    ├── README.md                 # lecture / concepts (~1500 words)
    ├── exercises.md              # typed shell commands the student runs
    └── quiz-<lesson-id>.json     # matches quiz.schema.v1.json for §7
```

Precedent: published 6-week course on bacterial genome assembly (CC-BY-SA 4.0) authored by 2 Herdr-delegated Pi agents — see `obs-2026-08-18-6-week-bacterial-genome-pipeline-course-built-via-2-herdr-de`. The layout matches `course-materials/<course>/<lesson>/{README,exercises,quiz-<id>.json}` and is a canonical reference for hand-authored courses that import into §6 + §7.

### `bin/quiz-import-pdf.py` — course importer

One CLI, four modes:

```bash
# 1. PDF chapter (pymupdf4llm)
bin/quiz-import-pdf.py --pdf textbook.pdf --pages 42-60 \
    --title "SAM flags" --lesson-id ch3-sam-flags \
    --out-dir course-materials/

# 2. Markdown / plain text on disk
bin/quiz-import-pdf.py --md chapter.md --title "SAM flags" \
    --lesson-id ch3-sam-flags --out-dir course-materials/

# 3. LLM-mediated fallback - pipe any text via stdin
#    (YouTube transcript, Notion export, lecture notes,
#    anything no deterministic parser handles)
cat transcript.txt | bin/quiz-import-pdf.py --llm-stdin \
    --title "SAM flags" --lesson-id ch3-sam-flags \
    --out-dir course-materials/
# ...then the agent reads the printed FILL_THIS.md directive on the
# next turn and fills the skeletons from source.txt.

# 4. Quiz JSON only - against an already-authored lesson
bin/quiz-import-pdf.py --quiz-from course-materials/<course>/<lesson>/exercises.md \
    --lesson-id ch3-sam-flags --title "SAM flags"
```

The importer never auto-generates answer keys — the agent or human fills `q` / `correct` / `answer_key` and validates against `quiz.schema.v1.json` before §7 sees it. This is the authoritative-hallucination rule documented in the script docstring.

### `quiz.schema.v1.json` — JSON Schema for §7

JSON Schema 2020-12. Versions as `herdr-skill+/quiz.v1`. Item kinds: `mcq`, `multi`, `preview`, `short`, `task` — one per `ask_user_question` call (never batch).

```bash
# Validate every quiz-<id>.json in the lesson directory
uv run --with jsonschema python3 -c "
import json, jsonschema, glob
schema = json.load(open('quiz.schema.v1.json'))
for qp in sorted(glob.glob('course-materials/**/quiz-*.json', recursive=True)):
    jsonschema.validate(json.load(open(qp)), schema)
    print(f'OK: {qp}')
"
```

### §6 / §7 intake rule

§6 will not start the gate loop until the lesson Markdown is on disk. §7 will not start the per-item loop until `quiz-<id>.json` is on disk and schema-valid. If either is missing on the first turn, the agent's first action is "import first" (clause documented in SKILL.md §6 + §7).

## Repo layout

```text
herdr-skill+/
├── SKILL.md                 # Workflow library: §1-§8 (read sections on demand)
├── quiz.schema.v1.json      # JSON Schema 2020-12 for §7 quiz interchange
├── README.md                # This file
├── docs-corpus/             # Offline snapshots of herdr CLI + 7 coding-agent harnesses
├── bin/
│   ├── quiz-import-pdf.py   # Course importer (4 modes; --llm-stdin fallback)
│   └── herdr-batch.py       # §1.6 batch ledger (new/set/show/todo)
├── LICENSE                  # MIT
└── .gitignore
```

There is intentionally **no** `pixi.toml` / `pixi.lock` / `scaffold-render.py` / `skill-update-check.py`. This skill is pure workflow + one Python CLI; dependency management happens upstream (the agent's runtime).

## Update check

```bash
# From a clone of this repo
git fetch origin
git rev-parse --verify HEAD                    # local HEAD
git rev-parse --verify origin/main             # upstream HEAD
```

| Verdict | Meaning |
|:--------|:--------|
| Match | UP-TO-DATE |
| Local ahead | Unpushed local commits; no action needed |
| Upstream ahead | Behind; consider re-pulling — compare against CHANGELOG below |
| `git fetch` failed | Offline / network issue; informational only |

## Hard guarantees

- **Workflow-only, no tool redefinition** — `SKILL.md` never restates `herdr_layout` / `herdr_pane` / `herdr_agent` parameters; it only orders calls and lists recovery paths. Drift rule at the bottom of SKILL.md enforces this.
- **Schema-grounded tool usage** — when the skill recommends a herdr CLI flag, the recommendation is grounded in `docs-corpus/herdr/` captures, not the agent's memory.
- **Push-UIs over poll loops** — every checkpoint that would otherwise need polling (tutorial-mode lesson gate, quiz-mode per-item grading) uses `ask_user_question` as a blocking gate (one tool call, zero LLM tokens while waiting). Polling loops with `bash sleep` + `herdr_pane read` are explicitly forbidden.
- **Markdown-first interchange** for human-authored course content; JSON is reserved for machine-graded quiz items at the lesson → quiz boundary.
- **Source-text sovereignty** — `bin/quiz-import-pdf.py --llm-stdin` accepts text the user pipes in; the script never *fetches* anything. Rights stay with the user.

## Changelog

### v0.16.0 (2026-09-24)

**Three operational rules adopted from community practice** (research into other herdr orchestration skills and parallel-agent workflows):

- **§2 verification economics.** Re-checking is for changed inputs, not ceremony: reuse a check's result when its inputs are unchanged (a handoff, re-read, or re-prompt does not invalidate evidence or require a second full suite); rerun only checks whose inputs changed, results went stale relative to later edits, or that contradict other evidence. Both failure modes named: redundant re-runs burn time budget; stale green results hide regressions.
- **§1 step 4 — staged dispatch for expensive or hard-to-verify batches.** When batch outputs are costly or slow to verify (image/doc generation, long migrations, no cheap pass/fail marker), send 1 first, verify it per §2 against a representative case, then dispatch the remainder — a systemic defect caught after dispatch is N× the damage.
- **§4.5 — unattended-yolo rule.** Explicitly unattended work (user-requested fire-and-forget, or long unwatched batches) launches with the harness's full-auto-approval flag from the §4.5 table instead of the intermediate default, because a blocked worker nobody is watching is a dead worker. Scoped: explicit user intent only (never chosen for convenience), task-owned paths only, one chat line disclosing the flag; secrets/credentials/outside-owned-paths → §5, never yolo; interactive sessions keep the intermediate default.

### v0.15.0 (2026-09-24)

**New §8 — multi-agent brainstorming mode (bidirectional).** Until now, "brainstorm with another agent" meant one-shot opinion collection (prompt → read → relay). §8 turns it into a real critique exchange, designed via online research (arXiv 2502.19130 *Voting or Consensus?*, Du et al. 2305.14325, arXiv 2502.19559 problem drift, kiloloop/brainstorm protocol) and a live two-round debate with a delegated Claude Code seat — which conceded 4 orchestrator critiques, revising the design mid-flight (the section was dogfooded before it existed):

- **Round structure** R0 independent draft (orchestrator writes its own BEFORE reading any seat — it is a participant; prevents anchoring) → R1 anonymized cross-critique (positions shuffled/unattributed, copied verbatim from seat-written fields, no tallies) → R2 decision round only if real disagreement remains. Hard cap 2 interaction rounds — add seats, not rounds (forced extra rounds reduce accuracy; groupthink).
- **Sycophancy countermeasures**: herdr's seat isolation IS the "no direct communication" channel the research recommends; `CHANGED: yes` must cite a named argument, and the orchestrator greps the saved relay file to verify it (fabricated = discounted); `RELAY FIDELITY` self-check per seat; the orchestrator never picks/paraphrases which arguments to relay (relay-author-bias fix from round 2).
- **Decision protocols by sub-mode**: divergent → Borda rank of pooled ideas (dissent = novelty); convergent/reasoning → plurality vote with ≥3 seats (2-seat ties go to the user; approval voting forbidden — 59% no-decision); convergent/factual → orchestrator verifies each EVIDENCE line; synthesis → merge with a Dissent section. The orchestrator never votes at any seat count.
- **Round barrier + blocked seats**: one §3 recovery attempt + 5-min window, then `excluded-r<N>` in the ledger (R0 position kept in Dissent, labelled "not critiqued", no vote); <2 active seats → ask the user.
- **Wiring**: seats are T3 read-only (§4.5); §4.6 ask-user gate extended (≥3 seats, any T2 seat, round past cap, hard-cap harness); one §1.6 ledger row per seat with a new `round` field; per-round artifacts `<ledger-dir>/<batch>/r<N>-<seat>.md` make a brainstorm resumable after compaction.

### v0.14.0 (2026-09-24)

**Batch execution, merge-back, and resumability** (from a Claude Code feature brainstorm; all flags verified against `docs-corpus/herdr/online-docs-0.8.2/`):

- **§1 step 4 — parallel batch dispatch.** With 2+ agents, a batch is only parallel if all prompts are sent before any wait begins: prompt each agent with `until: ["working"]` (returns on acceptance), then `herdr_agent wait` on every agent, servicing `blocked` first. Explicitly not fire-and-forget — every agent is still waited on and verified per §2.
- **§1 isolation note — native herdr worktrees.** `herdr worktree create --cwd <repo> --branch <task>-<agent> --label <agent> --no-focus` replaces raw `git worktree add` (workspaces grouped under the parent repo, `worktree.created` events, right cwd inherited for free); `herdr worktree remove --workspace <id>` for cleanup (never deletes the branch, `--force` is ask-first). Raw git kept as fallback.
- **New §1.5 worktree merge-back.** Gate on §2 verification → per-worktree diff+tests → merge smallest-diff-first → conflicts sent back to the owning agent (never resolved silently; escalate after 2 failed rounds) → cleanup that never deletes a branch without asking.
- **New §1.6 batch ledger + `bin/herdr-batch.py`.** Interruption-survivable JSON ledger (one row per agent: task, tier, harness, tab/pane IDs, worktree, session_id, convo_cursor, state, verified). Resume after herdr restart or context compaction by matching `herdr_agent list` rows on the `<task-slug>-<harness>` agent naming; lost agents re-dispatch only with user approval. Stdlib-only; `new` / `set` / `show --md` / `todo` subcommands.
- **§1 batch labeling.** Tabs renamed to the task slug (`herdr tab rename`), agents named `<task-slug>-<harness>` (doubles as the ledger join key), optional sidebar tokens via `herdr pane report-metadata`.
- **§6 expected-output precomputation.** Optional hidden-tab rehearsal on a throwaway copy of the scratch dir so lesson gates compare the student's output against *real* recorded output (success and error variants). Deterministic exercises only; the student still types every command.

Also reconciles README version drift again (README still showed v0.12.0 while SKILL.md was at v0.13.1 — the v0.13.x tab-first topology rule: 1 secondary agent → pane_split, 2+ → one new tab per agent, because 2+ splits squeeze panes to ~1/4 width).

### v0.12.0 (2026-09-19)

**§6 step-gate loop hardening** (from an external Claude Code review of SKILL.md):

- **Output-vs-step verification.** On `I did it`, the pane read is now checked against the step before explaining: the instructed command (or a valid variant) must appear as executed, and a command that should produce output must not be empty. Mismatches route to the error branch instead of being confidently narrated as correct. New anti-pattern: narrating unverified output.
- **Hardened `wait_output` fall-back.** The old output-anchored regex could not distinguish a completed silent command (`cd`, `export`, `set`) from a stale prompt. The fall-back now requires buffer growth past a pre-instruction line-count snapshot **plus** a trailing prompt match; residual limit (long-running silent commands) documented with two workarounds (wait on an output fragment, or an explicit `echo step-N-done` marker).
- **Tab-back cue.** With `focus: true` the student is in the side pane and may not think to return; the first instruction now must include one sentence on how to get back to the chat gate, repeated if the gate sits unanswered.
- **Retry cap.** After 3 consecutive `Something went wrong` answers on the same step, the identical gate is no longer re-issued; the loop offers skip / show-expected-result / keep-trying through the gate, and ends honestly if the student prefers. Never forced.

Also reconciles README version drift (README still showed v0.11.1 while SKILL.md was already v0.11.2 — the concurrent-write isolation decision rule shipped in v0.11.2).

### v0.11.2 (2026-09-16)

**Concurrent-write isolation decision rule in delegation step 1.** Added the decide-BEFORE-splitting rule: N writers > 1 → per-agent `git worktree add` with the worktree path as the pane's cwd; worktrees NOT needed for advisory-only agents, disjoint-directory, or serial work. Sharing one tree fails silently (index.lock races, contaminated test runs); worktree overhead fails loudly.

### v0.11.1 (2026-09-15)

**`quiz.schema.v1.json` schema fix.** Lowered `options.minItems` from 2 to 1. The schema's prose already said `short` and `task` items are "optional / forbidden" for `options` (they rely on the host's `Type something.` row at runtime), but the `minItems: 2` constraint made that impossible to express in practice — surfaced during the v0.11.0 cross-host test (item 4 of `/tmp/quiz-test/quiz-herdr-basics.json` is a `short` with no options). Same `quiz.v1` contract, just no longer self-contradictory.

### v0.11.0 (2026-09-15)

**§6 / §7 push-UI question tool is now host-aware.** Replaced every prose reference to `ask_user_question` (the Pi-rpiv-specific tool name) with the generic phrase "the host's push-UI question tool" and added a *Host equivalents* table at the top of §6 with the 5 host variants (Pi: `ask_user_question`; Claude Code: `AskUserQuestion` built-in; OpenCode: `task` permission policy `question`; RPC/ACP: native dialogs; non-interactive: tool removed). The *workflow contract* — one blocking tool call, zero LLM tokens while the student answers, two-option gate on §6 lesson steps, one tool call per §7 quiz item — is identical across hosts. Host-specific features (preview side-by-side, `Submit` review tab, per-question notes) degrade silently when not available. This makes §6 / §7 readable on Claude Code and OpenCode without breaking Pi behavior.

### v0.10.0 (2026-09-15)

**`bin/quiz-import-pdf.py --llm-stdin` LLM-mediated fallback.** User flagged the v0.9.0 importer as too rigid. New stdin mode writes source text to `<lesson>/source.txt`, scaffolds the lesson Markdown + quiz JSON, emits a `FILL_THIS.md` directive for the agent's next turn. CLI stays deterministic (no API key, no model dependency). Schema's `source.type` enum gains `"stdin"`. See `obs-2026-09-15-herdr-skill-plus-v0-10-0-llm-stdin-fallback`.

### v0.9.0 (2026-09-15)

**Markdown is the spine, JSON only at the lesson→quiz boundary.** User correction: course content was invented-as-JSON when the precedent `course-materials/bacterial-genome-pipeline/` already uses plain Markdown. Rewrote importer to emit `<lesson>/{README,exercises}.md` and `<lesson>/quiz-<id>.json`. Removed the buggy multi-lesson splitter. See `obs-2026-09-15-herdr-skill-plus-v0-9-0-markdown-spine-json-quiz-boundary`.

### v0.8.0 (2026-09-15)

**`quiz.schema.v1.json` + importer.** JSON Schema 2020-12 interchange for §7 quiz items (`mcq` / `multi` / `preview` / `short` / `task`); importer stub emits skeleton items the agent fills (never auto-grades). See `obs-2026-09-15-herdr-skill-plus-v0-8-0-quiz-schema-and-importer`.

### v0.7.0 (2026-09-15)

**§7 Quiz mode.** New section, same `ask_user_question` gate primitive as §6, different per-item loop. One `ask_user_question` per item (never batched, so the `Submit` review tab doesn't swallow per-item coaching). See `obs-2026-09-15-herdr-skill-plus-v0-7-0-quiz-mode-design`.

### v0.6.0 (2026-09-15)

**§6 tutorial mode rewrite.** Replaced the `bash sleep` + `herdr_pane read` polling loop (per-iteration LLM-token noise) with one blocking `ask_user_question` per lesson. Live-tested end-to-end with the user (4 lessons completed: `pwd`, `mkdir`+`cd`, `echo` + `> / >>`, `ls -la`). See `obs-2026-09-15-herdr-skill-plus-v0-6-0-tutorial-mode-live-test` and the gate-design note `obs-2026-09-15-herdr-skill-plus-v0-6-0-tutorial-mode-uses-ask-user-question-gate`.

### v0.5.0 → v0.4.x

Earlier versions (model discovery + provider preflight in §4.6, sudo pattern in §5, cross-agent delegation tests). See git log.

## Provenance & License

Built with the [bioinfo-skill-creator](https://github.com/cheahhl814/bioinfo-skill-creator) meta-skill (v1.1.0). The flat workflow-library layout (no preflight → run → qc sub-skill chain) is intentional — herdr-skill+ is a **single skill for one human conversational workflow**, not a batch pipeline.

Released under the MIT License — see the `LICENSE` file in this repository for details.
