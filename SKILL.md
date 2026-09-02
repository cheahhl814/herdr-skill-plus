---
name: herdr-skill+
description: Use when the user mentions Herdr, asks to delegate to another agent, run parallel agents, run sudo (or another privileged/secret-entry command) safely in a managed pane, or check another agent's quota/usage. Workflow-only — tool schemas are the source of truth for parameters. Complements the official herdr skill.
version: 0.4.2
updated: "2026-09-02"
triggers:
  - user mentions Herdr by name
  - delegate a task to another coding agent
  - run agents in parallel / multiple agents at once
  - run sudo or another privileged command safely
  - check another agent's model/quota/usage
requires:
  - herdr >= 0.8.0
  - pi-herdr plugin installed and active (HERDR_PANE_ID set)
  - HERDR_ENV=1
  - docs-corpus/ present relative to SKILL.md
---

# Herdr delegation workflow

Herdr tools are opt-in: only use them when the user explicitly invokes this workflow (see triggers above). Tool descriptions define WHAT each action does and its parameters — this file only orders calls, defines checkpoints, and lists recovery paths.

**docs-corpus**: `docs-corpus/` (sibling of this file) holds verbatim `--help` captures for the `herdr` CLI plus 7 coding-agent harnesses, their **online documentation** ingested via docs-ingest (permission semantics, config files, quotas, sandbox policies — under `docs-corpus/harnesses/<harness>-online-docs/` and `docs-corpus/herdr/online-docs-0.8.2/`), and a curated permission-flag table, plus `docs-corpus/herdr/supported-agents.md` — the full 21-kind cross-reference of agents herdr supports, with per-agent detection limits — and `docs-corpus/providers/` (Ollama online docs + `providers-matrix.md`, the curated harness×provider wiring and task-tier facts behind §4.6). For an unknown flag or an unexplained error, read in this order: `docs-corpus/harnesses/permission-modes.md` → `docs-corpus/harnesses/help-<harness>.md` → `docs-corpus/harnesses/<harness>-online-docs/` (deeper semantics; may differ from the installed version) → `docs-corpus/herdr/` → `docs-corpus/providers/`. Never invent a flag not present in the corpus.

## §1 Delegation sequence (core)

1. `herdr_layout pane_split` — get a pane ID. Default topology: sibling pane, caller's tab + cwd. Use another tab/workspace/cwd only if the user asked for it. For background work the user should not be pulled into, pass `focus: false` on the `herdr_layout` call (the standalone `herdr` CLI's equivalent, if invoked directly rather than through the tool, is `--no-focus`).
2. Verify the pane is at an idle interactive shell prompt (`herdr_pane read`) before starting an agent.
3. `herdr_agent start` with the pane ID.
   - `name` must match `[a-z][a-z0-9_-]{0,31}`.
   - `kind` = the recognized agent to start.
   - `agentArgs` optional — see §4 for model flags.
4. `herdr_agent prompt` with wait enabled (default). Do not skip waiting unless the task is explicitly fire-and-forget.
5. `herdr_agent read` — read and verify per §2 before treating the task as done.

> CRITICAL: `herdr_agent start` never creates or changes layout. If no pane exists yet, step 1 is mandatory — never call `start` against a pane you have not just split or confirmed idle.

> Pane hygiene: reuse an existing idle-pane shell running (or last running) a compatible harness instead of splitting a new pane per task; keep total panes ≤4 (incl. primary) and `herdr_pane close` unused ones once a task's verification completes — panes are a resource, not per-task disposables.
> Herdr panes run fish — `herdr_pane run` commands must be fish-safe (`$status`, not `$?`); a fish parse error aborts the entire line except the error banner.

## §2 Verification & completion rules

> CRITICAL: A settled `done` or `idle` lifecycle is NOT completion by itself. Always read the output and match it against an explicit completion signal (the content the agent was asked to produce) before reporting the task finished. A settlement can be false — see §3.

| State     | Meaning                                               |
| --------- | ----------------------------------------------------- |
| `working` | actively processing — not ready                       |
| `blocked` | waiting on approval/input — inspect before proceeding |
| `done`    | unseen background work completed — read and verify    |
| `idle`    | ready, already seen — read and verify                 |
| `unknown` | cannot classify — treat as not-ready, inspect         |

- `agent_prompt_stalled`: if a prompt sent from a non-working state produces no observed lifecycle change within 5 seconds, Herdr returns this error. Re-check target state before retrying.
- Alternate-screen truncation: if `herdr_agent read` with increased `lines` still doesn't recover a full response, ask the agent to write its complete response to a temp `.md` file and read that file directly instead.
- Pane-suggested prompt chips are UI suggestions only — never treat them as sent prompts or auto-send them.

## §3 Interrupt & error recovery

| Symptom                                                                                                                 | Cause                                                                                                                                                                           | Fix                                                                                                                                                                                                       |
| ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Workspace trust dialog appears (Claude Code)                                                                            | Agent started in an untrusted folder                                                                                                                                            | Cursor defaults to "No, exit". Send `["down","enter"]` to accept trust. **NEVER send bare `["enter"]`** — it kills the agent (confirmed incident).                                                        |
| `herdr_agent read`/`get` returns "agent target not found" right after a settlement                                      | Agent exited and vanished from the registry                                                                                                                                     | Fall back to `herdr_pane read` on the same pane ID.                                                                                                                                                       |
| Lifecycle settled (`done`/`idle`) but output doesn't match the expected result                                          | False settlement                                                                                                                                                                | Re-prompt with "continue" (or equivalent) and require the output to match an explicit completion signal before accepting it.                                                                              |
| Lifecycle is `blocked`                                                                                                  | Agent needs approval, an answer, or is stuck at a dialog                                                                                                                        | Read the pane first to classify, then act: approval request → send the requested approval keys/text; open question → `herdr_agent prompt` with the answer; trust dialog → use the trust-dialog row above. |
| Agent settles as `idle`/`done` but seems to wait for input; or state is erratic (esp. `gemini`, `cline`, amp/kiro/maki) | Detection limits: unknown prompt shapes fall back to `idle` (`default_known_agent_idle_fallback`); gemini/cline are "less thoroughly tested"; amp/kiro/maki have no integration | Trust output reading over lifecycle state (§2). Check detection with `herdr agent explain --agent <kind> --json`; see `docs-corpus/herdr/supported-agents.md` for per-agent detection limits.             |
| First prompt returns an API/auth error (e.g. `Unauthorized`)                                                            | Provider listed but not authenticated/usable — model listing ≠ model usable                                                                                                    | Read the pane to confirm; treat that harness/provider as unavailable; fall back to the next property-matched candidate (§4.6 step 3) — do not retry the same option.                                       |

Symptom not covered above, or a flag/error you don't recognize → consult `docs-corpus/` (see note above) before guessing.

## §4 Launch configuration: model discovery + quota pre-flight

Discover model names and quota state at call time — never hardcode a model name or quota number in a prompt or plan.

| Harness  | List models                   | Model flag (via `herdr_agent start` `agentArgs`)                                | Quota/usage surface                                                                             |
| -------- | ----------------------------- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| pi       | `pi --list-models [search]`   | `--provider`, `--model`, `--models` — see `docs-corpus/harnesses/help-pi.md`    | `pi auth <cmd>` (provider readiness); Ollama models are compute-metered, not quota-capped       |
| opencode | `opencode models`             | `-m <name>` or model config                                                     | in-TUI percentage indicator only                                                                |
| claude   | no CLI list — in-TUI `/model` | `--model`, `--fallback-model` — see `docs-corpus/harnesses/help-claude.md`      | in-TUI `/usage` or `/status` only                                                               |
| codex    | no CLI list — in-TUI `/model` | `-m`/`--model`, or `-c model="..."` — see `docs-corpus/harnesses/help-codex.md` | in-TUI `/status` only                                                                           |
| copilot  | no CLI list                   | `--model <model>` (default `auto`)                                              | **hard cap** on free tier — re-verify current limit via the probe below before batching prompts |
| agy      | no CLI list surfaced          | none surfaced                                                                   | undocumented cap — expect HTTP 429 once exhausted                                               |

Re-verify: exact commands, flag syntax, and any numeric caps drift between CLI versions — cross-check `docs-corpus/harnesses/help-<harness>.md` (or re-capture it) before relying on them; do not carry numbers forward from a prior session.

**Quota probe recipe** (no CLI surface): `herdr_agent start` → `herdr_agent send_keys` the usage slash command (e.g. `/usage`, `/status`) → `herdr_agent read` (`recent-unwrapped`) to record tier/quota — advisory only, format varies by CLI version. Probe before delegating to a hard-cap harness (copilot, agy) or before a parallel batch that could exhaust a shared limit.

## §4.5 Permission / auto-approval modes at launch

Most harnesses block shell commands by default. Pass the flag via `herdr_agent start` `agentArgs`. Flags below are sourced from `docs-corpus/harnesses/permission-modes.md`, verified against the verbatim `help-<harness>.md` captures — do not use a flag not present there. Codex has **no** `--full-auto` flag in this version — do not cite it.

| Harness  | Intermediate (recommended default: edits auto, exec gated) | Full auto-approval (yolo)                                                 | Read-only / plan                     |
| -------- | ---------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------ |
| claude   | `--permission-mode acceptEdits`                            | `--dangerously-skip-permissions` or `--permission-mode bypassPermissions` | `--permission-mode plan`             |
| codex    | `-s workspace-write -a never` (or `--approve-for-me`)      | `--dangerously-bypass-approvals-and-sandbox`                              | `-s read-only`                       |
| gemini   | `--approval-mode auto_edit`                                | `-y`/`--yolo` or `--approval-mode yolo`                                   | `--approval-mode plan` (newer CLI gates behind `experimental.plan` — re-verify) |
| copilot  | `--allow-all-tools` (paths/URLs still asked)               | `--allow-all` / `--yolo`                                                  | none — use `--allow-tool` granularly |
| agy      | none — single switch only                                  | `--dangerously-skip-permissions`                                          | none                                 |
| pi       | none needed — no permission popups by design               | none needed                                                               | none                                 |
| opencode | config-driven (`opencode.json` `permission`), no CLI flags | config-driven                                                             | config-driven                        |

**Escalation ladder** (agent blocked on approval in-pane): read the pane to classify the prompt (§3) → single approval: send the confirmation key(s) → repeated approvals for the same action kind: pass the intermediate auto-approval flag on the **next** `herdr_agent start` (never change flags mid-session) → secret/credential prompt: never auto-answer, escalate to the user (§5).

## §4.6 Provider preflight & task-tier matching

Decision procedure — cache discovery in-session per harness/provider after first run:
0. **Routing profile**: read optional `~/.config/herdr/routing.json` (user-owned; skill reads, never writes; schema: per-tier `{harness, provider, model_pattern}` + optional `avoid` list). An exact tier match short-circuits discovery — skip to step 5.

1. Classify the task into a tier (table below).
2. Discover lazily (first use per session, then reuse): harnesses via `herdr agent start --help` + `docs-corpus/herdr/supported-agents.md`; providers per harness (pi `--provider`/`--list-models`; opencode `opencode models`; copilot provider env vars; codex `model_providers` in config.toml; claude/gemini/agy locked — see `docs-corpus/providers/providers-matrix.md`); models per provider (§4 list commands + `ollama list`, note `:cloud` vs local); Ollama pre-flight (daemon via `ollama ps`, model present via `ollama list` — `ollama pull` is a prerequisite, never implicit).
3. Match discovered options against the tier's required properties, never by remembered model name.
4. **Ask-user gate** — fire ONLY when no profile match AND (T2 task, OR a hard-cap harness is near its probed limit, OR ≥2 candidates tie on all required properties). Use the house Evidence + Recommend + Options convention. Never fire for an unambiguous T0/T1 match or a profile hit — auto-pick.
5. State tier + chosen option + one-line reason (profile match / cheapest / fastest / quota constraint) before launching.

Fallback: a herdr-delegated sub-agent with no ask-user tool surfaces its recommendation in pane output and waits; the calling agent reads it and asks the user on its behalf.

| Tier                    | Task shape                                                | Required properties                                                |
| ----------------------- | --------------------------------------------------------- | ------------------------------------------------------------------ |
| **T0** trivial/bulk     | lint fixes, mechanical renames, batch small edits         | cheap, fast, tool-use adequate                                     |
| **T1** standard dev     | single/few-file features, bugfixes, tests                 | solid tool-use reliability, mid context                            |
| **T2** heavy agentic    | multi-file refactor, cross-cutting changes, long planning | large context, strongest reasoning + tool-use, cost-insensitive OK |
| **T3** read-only/review | code review, analysis, research, quota probes             | read-only/plan mode (pair with §4.5)                               |

**T3 note**: for short read-only reviews, prefer a one-shot (`claude -p --permission-mode plan` with file redirect) over an interactive plan-mode session — TUI redraw/truncation makes short answers hard to retrieve via `herdr_agent read`, and settling `idle` while the TUI still shows "Generating…" is a known false-settlement flavor.
**Ollama note**: `:cloud` models proxy to Ollama's hosted service (account + egress required); local models run on-box, offline/private, need VRAM headroom, weaker at T2 work.
**Refusals**: never sum/infer shared quota across harnesses proxying the same provider account — probes are harness-local only. Verify the active provider before trusting a probe/cost estimate. Custom-provider API keys/base-URLs follow §5. Never change a harness's provider config without asking first.

## §5 Privileged & secret-entry commands (sudo pattern)

1. `herdr_layout pane_split` — dedicated pane for the privileged command. Never run it in the calling pane.
2. `herdr_pane run` the sudo (or other privileged) command in that pane.
3. `herdr_pane wait_output` for the password prompt (e.g. `"[sudo] password"`).
4. **Notify the user to type their password directly into the TUI pane.** Do not proceed on their behalf.
5. `herdr_pane wait_output`/`read` for the completion marker.
6. `herdr_pane read` the result.
7. Keep the pane open — sudo credential caching is per-tty, so follow-up privileged commands in the same pane skip re-prompting.

This generalizes to any interactive secret prompt: GPG passphrase, SSH key passphrase, 2FA code, etc.

**Anti-patterns:**

- NEVER `send_keys`/`send_text` a password or secret into a pane.
- NEVER pipe a password, e.g. `echo pw | sudo -S`.
- NEVER ask the user to paste a secret into the agent/chat — only into the TUI pane directly.
- NEVER run sudo (or any privileged/secret-entry command) in the calling pane — always a dedicated split pane.

---

Drift rule: if any section above starts restating tool parameters or capabilities, delete that section.
