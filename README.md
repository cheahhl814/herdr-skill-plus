# herdr-skill+ — a delegation-workflow skill for coding agents

**Version 0.4.2** · A [progressive-disclosure skill](#what-is-a-skill) that teaches any coding agent how to **safely delegate tasks to other coding agents through [Herdr](https://github.com/herdr-dev/herdr)** — pane-first launch, verified completion, permission handling, provider/model pre-flight, and privileged-command discipline — backed by a **verbatim docs corpus** instead of remembered facts.

> **Design principle: workflow-only.** Tool descriptions own *what parameters exist*; this skill owns *sequencing, verification, recovery, and per-agent quirks*. It contains zero hardcoded model names or quota numbers — everything model-specific is discovered live or read from the corpus. If any section drifts back into restating tool parameters, delete it.

---

## Why this exists

Agents that shell out to other agents (Claude Code, Codex, Gemini CLI, OpenCode, Copilot CLI, pi, …) fail in predictable ways: they skip pane setup, treat a settled lifecycle as "done", invent CLI flags, sum quotas across harnesses that share an account, or type secrets into panes. This skill encodes the **counter-practices** as checklists and tables:

- **§1 Delegation sequence** — pane-first launch with pane hygiene (reuse idle panes, ≤4 total, close when done)
- **§2 Verification rules** — a settled `done`/`idle` is **never** completion; verify output against an explicit completion signal
- **§3 Interrupt & error recovery** — trust dialogs, false settlements, detection limits, auth errors
- **§4 Model discovery & quota pre-flight** — per-harness list commands, probe recipes, re-verify rules
- **§4.5 Permission/auto-approval flags** — verified per-harness launch flags (edits-auto / yolo / plan)
- **§4.6 Provider preflight & task-tier matching** — lazy cached discovery, optional user routing profile, T0–T3 property-based matching, ask-user gate
- **§5 Privileged & secret-entry commands** — the sudo pattern (dedicated pane, user types secrets, agent never touches them)

The **`docs-corpus/`** (109 files) holds verbatim `--help` captures for herdr + 7 harnesses, online documentation ingested from official sources, and curated fact tables — the rule is *never invent a flag not present in the corpus*.

## Install with your own agent (recommended)

Paste this prompt into your agent (Claude Code, OpenCode, pi, Goose, …) and let it perform the installation:

```text
Please install the "herdr-skill+" skill from https://github.com/cheahhl814/herdr-skill-plus.

1. Clone the repository to a temporary directory.
2. Copy its contents (SKILL.md and docs-corpus/) into your harness's skills
   directory under the folder name "herdr-skill+", e.g.:
   - Claude Code:  ~/.claude/skills/herdr-skill+/
   - OpenCode:     ~/.config/opencode/skills/herdr-skill+/
   - Goose:        ~/.config/goose/skills/herdr-skill+/
   - OpenClaw:     ~/.openclaw/skills/herdr-skill+/
   - pi:           ~/.pi/agent/skills/herdr-skill+/
   (use the equivalent skills directory for this harness; if several agents
   share the machine, copy the canonical folder once and symlink the rest)
3. Read the installed SKILL.md frontmatter "requires" and verify each item
   on this machine: herdr >= 0.8.0, HERDR_ENV=1, the pi-herdr plugin active,
   and docs-corpus/ present next to SKILL.md.
4. Report what you installed, where, and any unmet requirements.
   Do not invoke any herdr workflow beyond this verification.
```

### Manual install

```bash
git clone https://github.com/cheahhl814/herdr-skill-plus /tmp/herdr-skill-plus
mkdir -p ~/.claude/skills/herdr-skill+
cp -r /tmp/herdr-skill-plus/{SKILL.md,docs-corpus} ~/.claude/skills/herdr-skill+/
```

(For other harnesses, replace `~/.claude/skills/herdr-skill+` with your harness's skills path from the table above.)

## Requirements

| Requirement                                                                 | Why                                                                  |
| --------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `herdr` ≥ 0.8.0                                                             | pane/agent CLI the skill orchestrates                                |
| pi with the **pi-herdr plugin** active (`HERDR_PANE_ID` set, `HERDR_ENV=1`) | the skill targets agents already running inside a herdr-managed pane |
| `docs-corpus/` next to `SKILL.md`                                           | the skill refuses to guess flags — it reads the corpus instead       |

Optional: `~/.config/herdr/routing.json` — a **user-owned** routing profile (`{ "T2": { "harness": "claude", "provider": "…", "model_pattern": "…" }, "avoid": [...] }`). The skill reads it at preflight (§4.6 step 0) and never writes it. Absent file = default behavior.

## Repository structure

```
SKILL.md            the workflow (≤150 lines, checklists/tables only)
docs-corpus/        evidence corpus, two provenance tiers:
  herdr/              verbatim herdr CLI captures + online docs + supported-agents cross-reference
  harnesses/          per-harness help captures + online docs (permission semantics, quotas)
  providers/          alternative-provider corpus (Ollama cloud/local) + curated providers matrix
```

## Compatibility notes

- herdr supports **21 agent kinds**, but detection limits differ (gemini/cline are less thoroughly tested; some kinds have no integration) — see `docs-corpus/herdr/supported-agents.md`.
- herdr panes run the **fish** shell — keep `herdr_pane run` commands fish-safe.
- CLI flags drift between versions; the corpus is pinned to the installed versions and should be re-captured when you upgrade.

## Version history

| Version | Date       | Change                                                                                         |
| ------- | ---------- | ---------------------------------------------------------------------------------------------- |
| 0.1.0   | 2026-08-25 | initial workflow (delegation sequence, verification, recovery)                                 |
| 0.2.0   | 2026-09-02 | permission/auto-approval table, supported-agents cross-reference, docs corpus online-docs tier |
| 0.3.0   | 2026-09-02 | §4.6 provider discovery + T0–T3 task-tier matching, Ollama corpus                              |
| 0.4.0   | 2026-09-02 | preflight with lazy cached discovery, routing profile, ask-user gate                           |
| 0.4.1   | 2026-09-02 | pane hygiene, §3 auth-error recovery, fish note, gemini plan-mode drift fix                    |
| 0.4.2   | 2026-09-02 | renamed skill to `herdr-skill+` — it complements (does not replace) the official herdr skill |

## License

MIT — see [LICENSE](LICENSE).