# herdr-skill+

[![Version](https://img.shields.io/badge/version-0.10.0-blue)](#installation)
[![Type](https://img.shields.io/badge/type-agent%20skill-blueviolet)](#installation)
[![Built with](https://img.shields.io/badge/built%20with-bioinfo--skill--creator-orange)](https://github.com/cheahhl814/bioinfo-skill-creator)

Use when the user mentions Herdr, asks to delegate to another agent, run parallel agents, run sudo (or another privileged/secret-entry command) safely in a managed pane, check another agent's quota/usage, wants a hands-on CLI/bioinformatics tutorial in a side pane while you watch, runs a quiz / knowledge-check (5-6 items, MCQ + spot-the-bug + task) in a side pane, or imports a course from PDF/Markdown/any text source (with LLM-mediated fallback for non-PDF/non-MD). **Workflow-only** — tool schemas (`herdr_layout`, `herdr_pane`, `herdr_agent`) are the source of truth for parameters. Complements the [official herdr skill](https://github.com/herdr).

**Repository**: https://github.com/cheahhl814/herdr-skill-plus

> [!NOTE]
> Current version: **v0.10.0** (updated 2026-09-15). See [Changelog](#changelog) below for what changed.

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

> [!TIP]
> Every gated decision in §4-§7 surfaces back to the user via `ask_user_question` (Evidence + Recommend + Options) rather than auto-picking. This mirrors how Claude Code and OpenCode surface their permission prompts.

### Natural-language triggers

Trigger phrases (from SKILL.md `triggers:` frontmatter):

```text
- user mentions Herdr by name
- delegate a task to another coding agent
- run agents in parallel / multiple agents at once
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
├── SKILL.md                 # Workflow library: §1-§7 (read sections on demand)
├── quiz.schema.v1.json      # JSON Schema 2020-12 for §7 quiz interchange
├── README.md                # This file
├── docs-corpus/             # Offline snapshots of herdr CLI + 7 coding-agent harnesses
├── bin/
│   └── quiz-import-pdf.py   # Course importer (4 modes; --llm-stdin fallback)
├── params.json              # Skill metadata (name, version, owner)
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
