# herdr-skill+

[![Version](https://img.shields.io/badge/version-0.5.0-blue)](#-installation)
[![Type](https://img.shields.io/badge/type-agent%20skill-blueviolet)](#-installation)
[![Complements](https://img.shields.io/badge/complements-official%20herdr%20skill-informational)](#why-this-exists)

A progressive-disclosure skill that teaches any coding agent how to **safely delegate tasks to other coding agents through [Herdr](https://github.com/herdr-dev/herdr)** — pane-first launch, verified completion, permission handling, provider/model pre-flight, privileged-command discipline, and a human-driven CLI tutorial mode — backed by a **verbatim docs corpus** instead of remembered facts.

**Repository**: https://github.com/cheahhl814/herdr-skill-plus

> [!NOTE]
> Current version: **v0.5.0** (updated 2026-09-12).

> [!IMPORTANT]
> **Design principle: workflow-only.** Tool descriptions own *what parameters exist*; this skill owns *sequencing, verification, recovery, and per-agent quirks*. It contains zero hardcoded model names or quota numbers — everything model-specific is discovered live or read from the corpus. If any section drifts back into restating tool parameters, delete it.

## Contents

- [Why this exists](#why-this-exists)
- [Installation](#-installation)
- [Usage](#-usage)
- [Workflow sections](#-workflow-sections)
- [Docs corpus](#-docs-corpus)
- [Repository layout](#-repository-layout)
- [Hard guarantees](#-hard-guarantees)
- [Compatibility notes](#compatibility-notes)
- [License](#license)

## Why this exists

Agents that shell out to other agents (Claude Code, Codex, Gemini CLI, OpenCode, Copilot CLI, pi, …) fail in predictable ways: they skip pane setup, treat a settled lifecycle as "done", invent CLI flags, sum quotas across harnesses that share an account, delegate in fire-and-forget mode for their own convenience rather than the user's, or type secrets into panes. This skill encodes the **counter-practices** as checklists and tables — see [Workflow sections](#-workflow-sections) below.

## 🚀 Installation

This is an **agent skill**, not a user-facing library. The recommended install path is to let your AI agent import it.

**Option A — give your agent this prompt (recommended):**

```text
Please install the "herdr-skill+" skill from
https://github.com/cheahhl814/herdr-skill-plus.

1. Clone the repository to a temporary directory.
2. Copy its contents (SKILL.md and docs-corpus/) into your harness's
   skills directory (the path your agent watches for skills) under the
   folder name "herdr-skill+". If several agents share the machine, copy
   the canonical folder once and symlink the rest.
3. Read the installed SKILL.md frontmatter "requires" and verify each
   item on this machine: herdr >= 0.8.0, HERDR_ENV=1, the pi-herdr plugin
   active, and docs-corpus/ present next to SKILL.md.
4. Report what you installed, where, and any unmet requirements.
   Do not invoke any herdr workflow beyond this verification.
```

**Option B — manual install:**

```bash
git clone https://github.com/cheahhl814/herdr-skill-plus.git /tmp/herdr-skill-plus
mkdir -p your-agent-skills-dir/herdr-skill+
cp -r /tmp/herdr-skill-plus/{SKILL.md,docs-corpus} your-agent-skills-dir/herdr-skill+/
```

Replace `your-agent-skills-dir` with the skills directory your harness watches (Claude Code, OpenCode, Goose, OpenClaw, pi, etc. each use their own path).

> [!TIP]
> Optional: `~/.config/herdr/routing.json` — a **user-owned** routing profile (`{ "T2": { "harness": "claude", "provider": "…", "model_pattern": "…" }, "avoid": [...] }`). The skill reads it at preflight (§4.6 step 0) and never writes it. Absent file = default behavior.

## 💡 Usage

The skill is opt-in: it only activates when the user's request matches one of its triggers.

### Natural-language prompts that trigger the skill

```text
delegate this task to another coding agent
run three agents in parallel on these files
run this sudo command safely
check codex's quota before I batch these prompts
teach me the samtools CLI hands-on in a side pane
```

### Requirements

| Requirement | Why |
|:--|:--|
| `herdr` ≥ 0.8.0 | pane/agent CLI the skill orchestrates |
| pi-herdr plugin active (`HERDR_PANE_ID` set, `HERDR_ENV=1`) | the skill targets agents already running inside a herdr-managed pane |
| `docs-corpus/` next to `SKILL.md` | the skill refuses to guess flags — it reads the corpus instead |

## 🔬 Workflow sections

| # | Section | Covers |
|:--|:--|:--|
| §1 | Delegation sequence | pane-first launch, pane hygiene (reuse idle panes, ≤4 total, close when done), non-interactive-mode caveats |
| §2 | Verification rules | a settled `done`/`idle` is **never** completion; verify output against an explicit completion signal |
| §3 | Interrupt & error recovery | trust dialogs, false settlements, detection limits, auth errors |
| §4 | Model discovery & quota pre-flight | per-harness list commands, probe recipes, re-verify rules |
| §4.5 | Permission / auto-approval flags | verified per-harness launch flags (edits-auto / yolo / plan) |
| §4.6 | Provider preflight & task-tier matching | lazy cached discovery, optional user routing profile, T0–T3 property-based matching, ask-user gate |
| §5 | Privileged & secret-entry commands | the sudo pattern (dedicated pane, user types secrets, agent never touches them) |
| §6 | CLI/bioinformatics tutorial mode | inverted §1 — a human-typed pane the agent watches and coaches, never drives; a blocking continuous-monitoring loop means the user only types in the pane, never re-prompts in chat |

> [!TIP]
> Read `SKILL.md` directly for the full checklists and recovery tables — this README only orients you to what exists.

## 📚 Docs corpus

Tool and flag usage is grounded in the offline `docs-corpus/` snapshots — the agent reads these instead of guessing:

| Tier | Contents |
|:--|:--|
| Source 1 — verbatim CLI captures | `--help` output for `herdr` and 7 coding-agent harnesses, pinned to the installed version |
| Source 2 — online docs | richer context (concepts, config files, quotas, permission semantics) ingested from official sites/repos |
| Source 3 — community marketplace | self-tagged, unreviewed third-party Herdr plugins that extend the workflow — candidates only, never installed automatically |

`docs-corpus/herdr/supported-agents.md` cross-references all 21 agent kinds Herdr supports, with per-agent detection limits.

## 📁 Repository layout

```text
SKILL.md            the workflow (checklists/tables only)
docs-corpus/         evidence corpus, three provenance tiers
  herdr/              verbatim herdr CLI captures + online docs + supported-agents cross-reference + related-plugins pointer
  harnesses/          per-harness help captures + online docs (permission semantics, quotas)
  providers/          alternative-provider corpus (Ollama cloud/local) + curated providers matrix
```

## 🔒 Hard guarantees

- **Workflow-only** — this skill never restates tool parameters; it owns sequencing, verification, and recovery.
- **Docs-grounded tool usage** — flags come from `docs-corpus/`, never from the agent's memory.
- **Never invent a flag** not present in the corpus — re-capture instead of guessing when a harness updates.
- **Pane hygiene enforced** — reuse idle panes, cap total panes, close when a task's verification completes.
- **No fire-and-forget by default** — background delegation only when the user explicitly asks for it, never for the agent's own convenience.

## Compatibility notes

- herdr supports **21 agent kinds**, but detection limits differ (gemini/cline are less thoroughly tested; some kinds have no integration) — see `docs-corpus/herdr/supported-agents.md`.
- herdr panes run the **fish** shell — keep pane-run commands fish-safe.
- CLI flags drift between versions; the corpus is pinned to the installed versions and should be re-captured after an upgrade.
- Community plugins in `docs-corpus/herdr/related-plugins.md` are unreviewed and version-sensitive — re-verify compatibility with your herdr version before relying on one.

## License

Released under the MIT License — see [LICENSE](LICENSE).
