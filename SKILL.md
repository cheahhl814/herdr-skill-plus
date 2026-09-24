---
name: herdr-skill+
description: Use when the user mentions Herdr, asks to delegate to another agent, run parallel agents, run sudo (or another privileged/secret-entry command) safely in a managed pane, check another agent's quota/usage, wants a hands-on CLI/bioinformatics tutorial in a side pane while you watch, run a quiz / knowledge-check (5-6 items, MCQ + spot-the-bug + task) in a side pane, or import a course from PDF/Markdown/any text source (with LLM-mediated fallback for non-PDF/non-MD) into a Markdown spine with optional quiz JSON per lesson. Workflow-only — tool schemas are the source of truth for parameters. Complements the official herdr skill.
version: 0.13.1
updated: "2026-09-24"
triggers:
  - user mentions Herdr by name
  - delegate a task to another coding agent
  - run agents in parallel / multiple agents at once
  - run sudo or another privileged command safely
  - check another agent's model/quota/usage
  - teach/tutor the user on CLI or bioinformatics commands hands-on in a side pane
  - run a quiz / knowledge-check in a side pane (MCQ, spot-the-bug, task items)
  - import a course from PDF / Markdown into a Markdown spine (lesson = README+exercises+quiz-N.json)
  - import a course from any text source via bin/quiz-import-pdf.py --llm-stdin (YouTube transcript, Notion export, lecture notes)
  - author a new course or extend an existing one in the Markdown spine + JSON quiz schema
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

1. **Decide the topology BEFORE creating layout.** Count how many secondary agents the task will run concurrently.
   - **1 secondary agent** → `herdr_layout pane_split` — get a pane ID. Default topology: sibling pane, caller's tab + cwd. Use another tab/workspace/cwd only if the user asked for it. For background work the user should not be pulled into, pass `focus: false` on the `herdr_layout` call (the standalone `herdr` CLI's equivalent, if invoked directly rather than through the tool, is `--no-focus`).
   - **2+ secondary agents** → do NOT split a second pane. Every split beyond the first shrinks each pane's share of the screen; at 2+ splits a pane drops to roughly 1/4 width, where agent output is effectively unreadable — both for you when verifying via `herdr_agent read`/`herdr-convo` and for the user watching the TUI. Instead, create **one new tab per agent** (`herdr_layout tab_create`; each new tab comes with its own root pane — no extra split needed) and run steps 2–5 below against each tab's root pane. Tabs keep every agent full-width; the user switches tabs instead of squinting at quarter-panes. Set each tab's `cwd` the same way you would have set the pane's (worktree/scratch dirs per the concurrent-write isolation rule below); pass `focus: false` for background batches the user shouldn't be pulled into.
   
   > **Concurrent-write isolation (decide BEFORE splitting):** if two or more agents will WRITE to the same git repo concurrently, share one working tree — `git worktree add ../<repo>-wt-<agent> -b <branch>` per writing agent and pass that worktree path as the pane's cwd; integrate at merge time, where conflicts are visible instead of silently interleaved. Sharing a tree fails silently (index.lock races, contaminated test runs from a neighbor's half-finished edits, clobbered build/cache state), while worktree overhead fails loudly. Worktrees are NOT needed for advisory/brainstorm agents that write only to /tmp briefs, disjoint directories (one agent per subtree, explicit ownership), or serial work (one writer, others idle) — there a worktree is pure ceremony and adds a stale-base problem. Rule of thumb: N writers > 1 → isolate; N readers / 1 writer → share the tree.
2. Verify the pane is at an idle interactive shell prompt (`herdr_pane read`) before starting an agent.
3. `herdr_agent start` with the pane ID.
   - `name` must match `[a-z][a-z0-9_-]{0,31}`.
   - `kind` = the recognized agent to start.
   - `agentArgs` optional — see §4 for model flags.
4. `herdr_agent prompt` with wait enabled (default). Do not skip waiting unless the **user** explicitly asked for fire-and-forget — never choose it yourself for convenience, since it removes the user's only visibility into the secondary agent.
5. `herdr_agent read` (or **herdr-convo**, below, for claude/codex/opencode/pi) — read and verify per §2 before treating the task as done, then relay the secondary agent's actual output (not just "done") back to the user — they cannot see the pane unless they look at it themselves.

> **zoetrope plugin** (source 3, `docs-corpus/herdr/related-plugins.md`) — if installed, this is the user's own answer to "I can't see what the secondary agent is doing" (§1 step 4's concern): focusing a claude/codex agent pane and pressing `prefix+shift+z` opens a live flow-graph overlay of that session for the **user** to watch directly — it doesn't change what you (the calling agent) do, but mention it exists when delegating so the user knows they have a real-time option beyond waiting for your relay.
> 
> Non-interactive/print-mode invocations (`-p`, `exec`, `--print`, etc., run via `herdr_pane run` instead of `herdr_agent`) have no lifecycle, no §2 states, and none of the §3 recovery paths — a blocked or approval-seeking sub-agent just hangs silently with nothing to read. Reserve this mode for the T3 one-shot case in §4.6 (short, read-only, unlikely to need approval); default to interactive `herdr_agent` delegation for everything else so state and output stay observable.

> CRITICAL: `herdr_agent start` never creates or changes layout. If no pane exists yet, step 1 is mandatory — never call `start` against a pane you have not just split or confirmed idle.

> Pane hygiene: reuse an existing idle-pane shell running (or last running) a compatible harness instead of splitting a new pane per task; keep total panes ≤2 per tab (incl. primary) — a batch of 2+ agents goes into new tabs, not more panes (step 1) — and `herdr_pane close` unused ones once a task's verification completes — panes are a resource, not per-task disposables.
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
- Alternate-screen truncation: if `herdr_agent read` with increased `lines` still doesn't recover a full response, first try **herdr-convo** (below) if the harness is claude/codex/opencode/pi — it reads the session transcript file directly, bypassing terminal rendering entirely. Otherwise ask the agent to write its complete response to a temp `.md` file and read that file directly.
- Pane-suggested prompt chips are UI suggestions only — never treat them as sent prompts or auto-send them.

**herdr-convo plugin** (source 3, `docs-corpus/herdr/related-plugins.md`) — if installed, prefer it over `herdr_agent read`/`herdr_pane read` for **claude, codex, opencode, pi** (not gemini/copilot/agy — unsupported). Verified 2026-09-12: `node <plugin-root>/src/cli.ts latest <pane_id> --text` returned this session's own last turn verbatim, read straight from `~/.claude/projects/.../<session>.jsonl` (or the codex/opencode/pi equivalent), not the terminal. This is a strict upgrade over pane-scraping — no alternate-screen truncation, no ANSI noise, structured JSON by default (`--text` for plain). Two calls matter for this workflow:

- `latest <target> --text` — the agent's last full response as plain text. Use this for §2's completion-signal check instead of `herdr_agent read` when the harness is supported.
- `read <target> --cursor <C>` — only turns since the last-seen cursor; use this for polling a long-running delegated task incrementally instead of repeated full pane reads. `target` is a Herdr pane/agent id; error codes are JSON (`cursor_stale`, `session_not_found`, `no_agent_session`, `herdr_unavailable`, `unsupported_agent`) — fall back to `herdr_agent read` on any of these rather than retrying blind.

**zoetrope plugin** (source 3) — the `zoe inspect <session_id>` headless mode (claude/codex only, needs a session id — get one from `herdr-convo locate <pane>`) gives a cheap structured health check without full text: agent status, model, and tool-call counts split `✓`/`✗`/`⏳`. Verified 2026-09-12: correctly reported this session's own 90 tool calls (82✓ 7✗ 1⏳). Use it as a fast first check for "is something stuck/erratic" before spending a full `herdr-convo latest --text` read — a nonzero `⏳` with no lifecycle change over time is a stronger stuck-signal than lifecycle state alone. It does not take a pane id directly, only a session id or file path.

## §3 Interrupt & error recovery

| Symptom                                                                                                                 | Cause                                                                                                                                                                           | Fix                                                                                                                                                                                                       |
| ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Workspace trust dialog appears (Claude Code)                                                                            | Agent started in an untrusted folder                                                                                                                                            | Cursor defaults to "No, exit". Send `["down","enter"]` to accept trust. **NEVER send bare `["enter"]`** — it kills the agent (confirmed incident).                                                        |
| `herdr_agent read`/`get` returns "agent target not found" right after a settlement                                      | Agent exited and vanished from the registry                                                                                                                                     | Fall back to `herdr_pane read` on the same pane ID.                                                                                                                                                       |
| Lifecycle settled (`done`/`idle`) but output doesn't match the expected result                                          | False settlement                                                                                                                                                                | Re-prompt with "continue" (or equivalent) and require the output to match an explicit completion signal before accepting it.                                                                              |
| Lifecycle is `blocked`                                                                                                  | Agent needs approval, an answer, or is stuck at a dialog                                                                                                                        | Read the pane first to classify, then act: approval request → send the requested approval keys/text; open question → `herdr_agent prompt` with the answer; trust dialog → use the trust-dialog row above. |
| Agent settles as `idle`/`done` but seems to wait for input; or state is erratic (esp. `gemini`, `cline`, amp/kiro/maki) | Detection limits: unknown prompt shapes fall back to `idle` (`default_known_agent_idle_fallback`); gemini/cline are "less thoroughly tested"; amp/kiro/maki have no integration | Trust output reading over lifecycle state (§2). Check detection with `herdr agent explain --agent <kind> --json`; see `docs-corpus/herdr/supported-agents.md` for per-agent detection limits.             |
| First prompt returns an API/auth error (e.g. `Unauthorized`)                                                            | Provider listed but not authenticated/usable — model listing ≠ model usable                                                                                                     | Read the pane to confirm; treat that harness/provider as unavailable; fall back to the next property-matched candidate (§4.6 step 3) — do not retry the same option.                                      |

Symptom not covered above, or a flag/error you don't recognize → consult `docs-corpus/` (see note above) before guessing.

## §4 Launch configuration: model discovery + quota pre-flight

Discover model names and quota state at call time — never hardcode a model name or quota number in a prompt or plan.

| Harness  | List models                   | Model flag (via `herdr_agent start` `agentArgs`)                                | Quota/usage surface                                                                          |
| -------- | ----------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| pi       | `pi --list-models [search]`   | `--provider`, `--model`, `--models` — see `docs-corpus/harnesses/help-pi.md`    | `pi auth <cmd>` (provider readiness); Ollama models are compute-metered, not quota-capped    |
| opencode | `opencode models`             | `-m <name>` or model config                                                     | in-TUI percentage indicator only                                                             |
| claude   | no CLI list — in-TUI `/model` | `--model`, `--fallback-model` — see `docs-corpus/harnesses/help-claude.md`      | **herdr-agent-quota** JSON, if installed (below); else in-TUI `/usage` or `/status`          |
| codex    | no CLI list — in-TUI `/model` | `-m`/`--model`, or `-c model="..."` — see `docs-corpus/harnesses/help-codex.md` | herdr-agent-quota only covers ChatGPT-subscription auth, not API-key auth — in-TUI `/status` |
| copilot  | no CLI list                   | `--model <model>` (default `auto`)                                              | **hard cap** on free tier — no plugin coverage (see below) — re-verify via the probe recipe  |
| agy      | no CLI list surfaced          | none surfaced                                                                   | **herdr-agent-quota** JSON, if installed (below); else undocumented cap, expect HTTP 429     |

Re-verify: exact commands, flag syntax, and any numeric caps drift between CLI versions — cross-check `docs-corpus/harnesses/help-<harness>.md` (or re-capture it) before relying on them; do not carry numbers forward from a prior session.

**Quota probe recipe** (no CLI surface, all harnesses): `herdr_agent start` → `herdr_agent send_keys` the usage slash command (e.g. `/usage`, `/status`) → `herdr_agent read` (`recent-unwrapped`) to record tier/quota — advisory only, format varies by CLI version. Probe before delegating to a hard-cap harness (copilot, agy) or before a parallel batch that could exhaust a shared limit.

**herdr-agent-quota plugin** (source 3, `docs-corpus/herdr/related-plugins.md`) — if installed and configured (`herdr plugin action invoke configure --plugin herdr-agent-quota`, not the raw binary — see below), `claude`/`agy` quota is collected passively by a statusLine/hook the harness itself invokes every turn, not by polling. Read it directly instead of the `refresh`/`dashboard` subcommands (those need pane/session context this skill's ad hoc CLI calls don't have, and return `unavailable` even with real data present):

```
cat ~/.local/state/herdr/plugins/herdr-agent-quota/claude-statusline.observation.json   # claude
cat ~/.local/state/herdr/plugins/herdr-agent-quota/agy-statusline.observation.json      # agy
```

Each file's `snapshot.windows` gives `five_hour`/`weekly` `used_percent`/`remaining_percent` + `resets_at`; absent file = that harness hasn't run a turn since the hook was installed yet. Coverage gaps, verified 2026-09-12 on this machine: no `copilot`/`pi`/`opencode` support at all — still use the scrape recipe for those; `codex` only works with ChatGPT-subscription auth, not API-key auth.

Enabling this for `claude`/`agy` writes `~/.claude/settings.json` / `~/.gemini/antigravity-cli/settings.json` (a `statusLine` block only, verified minimal diff) — a standing-config change: ask the user before enabling it, and never run `configure --apply` yourself if `~/.claude/settings.json` is your own config (Claude Code's self-modification guard blocks that, and the plugin separately refuses the raw binary — must go through `herdr plugin action invoke configure --plugin herdr-agent-quota`). Direct the user to run it in a pane.

## §4.5 Permission / auto-approval modes at launch

Most harnesses block shell commands by default. Pass the flag via `herdr_agent start` `agentArgs`. Flags below are sourced from `docs-corpus/harnesses/permission-modes.md`, verified against the verbatim `help-<harness>.md` captures — do not use a flag not present there. Codex has **no** `--full-auto` flag in this version — do not cite it.

| Harness  | Intermediate (recommended default: edits auto, exec gated) | Full auto-approval (yolo)                                                 | Read-only / plan                                                                |
| -------- | ---------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| claude   | `--permission-mode acceptEdits`                            | `--dangerously-skip-permissions` or `--permission-mode bypassPermissions` | `--permission-mode plan`                                                        |
| codex    | `-s workspace-write -a never` (or `--approve-for-me`)      | `--dangerously-bypass-approvals-and-sandbox`                              | `-s read-only`                                                                  |
| gemini   | `--approval-mode auto_edit`                                | `-y`/`--yolo` or `--approval-mode yolo`                                   | `--approval-mode plan` (newer CLI gates behind `experimental.plan` — re-verify) |
| copilot  | `--allow-all-tools` (paths/URLs still asked)               | `--allow-all` / `--yolo`                                                  | none — use `--allow-tool` granularly                                            |
| agy      | none — single switch only                                  | `--dangerously-skip-permissions`                                          | none                                                                            |
| pi       | none needed — no permission popups by design               | none needed                                                               | none                                                                            |
| opencode | config-driven (`opencode.json` `permission`), no CLI flags | config-driven                                                             | config-driven                                                                   |

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

## §6 CLI/bioinformatics tutorial mode (human-driven pane)

Inverts §1: the pane runs a plain shell that the **user** types into, not an AI agent. Your job is set the exercise, gate on milestone completion, and coach — never to type the lesson commands for them, never to busy-poll the pane.

The natural failure mode of the previous design was LLM-token noise: every `bash sleep` + `herdr_pane read` iteration produced a fresh streaming reply while the student thought. The fix below uses a **push-UI question tool** as the **only** gating primitive — a single blocking tool call the student resolves by tabbing back to the chat and pressing `1` or `2`, with zero LLM tokens in between. (This mirrors how Claude Code and OpenCode surface permission prompts: a push UI, not a poll loop.)

**Host equivalents of the push-UI question tool.** §6 and §7 call this tool "`ask_user_question`", but the exact tool name and schema differ per host. Use whichever your host exposes; the workflow contract is identical:

| Host                                            | Tool                                                                                     | Surface                                                                                                                                                                                                    |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pi** (this skill's primary host)              | `ask_user_question` (from `@juicesharp/rpiv-ask-user-question`)                          | Tabbed TUI overlay: typed options, `multiSelect` checkboxes, `preview` side-by-side ≥100 cols, `Type something.` free-text, `Submit` review tab when ≥2 questions, per-question `n` notes                  |
| **Claude Code**                                 | `AskUserQuestion` (built-in)                                                             | Permission-card UI; `multiSelect` supported; *no* `preview`; notes / `Type something.` not separately surfaced                                                                                             |
| **OpenCode**                                    | `task` permission policy `question` (built-in)                                           | Inline ask during execution; the model surfaces a single question at a time                                                                                                                                |
| **RPC/ACP hosts** (VS Code pendant, Zed, Paseo) | `ask_user_question` if installed; otherwise the host's native `select` + `input` dialogs | Native dialogs one-question-at-a-time; no tab bar, no Submit review, no notes; previews truncated to 600 chars and folded into the dialog title                                                            |
| **Non-interactive run** (CI, headless)          | —                                                                                        | Tool is removed from the model list (Pi's `before_agent_start` reconciler, per `ask_user_question`'s `hosts.md`). §6 falls back to a single bounded `wait_output`; §7 has no equivalent and ends the quiz. |

Whenever §6 or §7 below says "`ask_user_question`", read it as "your host's push-UI question tool." The *workflow contract* — one blocking tool call, zero LLM tokens while the student answers, two-option canonical gate on lesson steps, one tool call per quiz item — applies identically across hosts. Host-specific *features* (preview, notes, Submit tab) degrade silently when not available; do not block on them.

**Course content intake.** §6 walks the student through a lesson whose source is plain Markdown. Three paths converge on this shape:

- **Human-authored**: existing course layouts (e.g. `course-materials/<course>/week-N-*/{README,exercises,checklist}.md`, see `obs-2026-08-18-6-week-bacterial-genome-pipeline-course-built-via-2-herdr-de`) — open `week-N-*/exercises.md`, read the commands top to bottom, issue them one at a time as chat instructions, gate after each.
- **Imported from PDF / Markdown on disk**: `bin/quiz-import-pdf.py --pdf textbook.pdf --pages 42-60 ...` or `--md chapter.md ...`. Parsers handle structure; LLM is not in the loop.
- **Imported from anything else** (YouTube transcript copy-paste, Notion export, lecture notes, DOCX after `pandoc` conversion to plain text, prose dictated from audio): `cat source.txt | bin/quiz-import-pdf.py --llm-stdin ...`. The script writes the text to `<lesson>/source.txt`, scaffolds the lesson Markdown + quiz JSON, and emits a `FILL_THIS.md` directive you read in the next chat turn. You (the agent) fill README + exercises + quiz items against `source.txt`; the user retains ownership of the text — the script never *fetches*. This is the LLM-mediated fallback for sources no deterministic parser handles.

§6's loop below assumes Markdown is on disk in front of you. If it isn't, your first turn is "import the source first" — not "import and then start teaching in the same turn." The `--llm-stdin` mode produces a `FILL_THIS.md`; that directive IS your first turn. Read it, fill the skeletons, validate the quiz JSON against `quiz.schema.v1.json`, then start §6.

1. `herdr_layout pane_split` with `focus: true` (the user needs to interact with this pane directly — the opposite default from §1's background delegation). cwd should be a scratch/sandbox directory; confirm one exists or create it before the first exercise so a typo can't touch real project state.
2. `herdr_pane read` — confirm idle shell prompt and note its shape (e.g. `$ `, `❯ `, `~/scratch> `). You are NOT going to regex-match it for gating in the loop below — `herdr_pane wait_output` matches against *existing* output too and returns on the stale pre-existing prompt before the student has typed anything (verified 2026-09-14). Polling to dodge that bug is exactly what produces per-iteration noise. Use the push-UI question tool (see *Host equivalents* above) instead.
3. Give the student the first instruction in chat (e.g. "run `samtools view -H aln.bam`"). Plain language, not a command you send yourself. Because the pane was split with `focus: true` (step 1), the student is now *in the side pane and may not think to come back* — include one sentence with the first instruction telling them how to return (e.g. "…then tab back to the chat and answer the prompt"), and repeat that cue whenever the gate sits unanswered for a long stretch. Then go straight into the gate below **in the same turn** — do not end your turn and wait for the student's next chat message; that defeats "the student shouldn't have to re-prompt."

**Step-gate loop** (repeat until an end condition below is hit):

   a. The push-UI question tool with exactly one question, two options, in this order:

      - `I did it (next lesson)` — description: "I ran the command in the side pane. Move on to the next step."
      - `Something went wrong` — description: "I got an error or the output looks off — coach me through it before continuing."
    
      Header chip: `Lesson N done` (≤16 chars). Mark the recommended option with `(Recommended)` on its label so the student can press Enter for the happy path. Add a note in the option description only if the lesson specifically requires one (e.g. paste an error).
    
      The questionnaire is a single blocking tool call — once it is on screen, the agent emits **zero** further tokens until the student answers. The chat pane stays quiet while they work in the side pane, which is the whole point.

   b. **On `I did it`**: `herdr_pane read` (source `visible` for the most recent command's output). **Before explaining anything, check the read against the step**: the command the student was told to run (or a valid variant form) must actually appear as the executed command in the buffer, and a command that should produce output must not be empty. If the evidence doesn't match — a different command ran, no new output since the previous step, empty where output was due — do NOT narrate it as a success; route to the error branch (c) below, treating the mismatch as "something went wrong until explained". A valid variant form is not a mismatch — if in doubt, ask which command they ran rather than blocking. Then explain the output in chat in 2-4 sentences, issue the next instruction **and immediately re-issue the same gate** — keep the student inside the same turn so they don't have to prompt you between lessons.

   c. **On `Something went wrong`**: `herdr_pane read` (source `recent-unwrapped`, generous `--lines`) to see what happened. Narrate the diagnosis — *what* went wrong, *why* — then either (i) give a corrected instruction and re-issue the same gate, or (ii) end the lesson if the error is structural (wrong shell, missing tool) and recommend re-setup.

      **Retry cap**: count consecutive `Something went wrong` answers on the *same* step. After 3 in a row, the loop is stuck on the student's environment or the step's phrasing, not the concept — stop re-issuing the identical gate. Instead, offer a way out through the gate itself (options like "Skip this step", "Show me the expected result", "Keep trying"), and end the lesson honestly if the student prefers to stop. Never silently repeat the same instruction a 4th time, and never force a skip — it's the student's call.

   d. If an instruction would invoke sudo or another secret prompt, switch to the §5 pattern for that one step, then resume the loop.

**End the loop** (and your turn) only when: the lesson plan is exhausted, or the student's answer or a chat message signals they're done or stuck ("done", "quit", "I need help"). Then `herdr_pane close` — don't leave a teaching pane open past the session (pane-hygiene budget in §1 still applies).

**Fall-back when the push-UI question tool is unavailable**: in non-interactive hosts (RPC/ACP without a chat dialog or non-TTY runs) the tool is stripped from the model's tool list. In that case the canonical alternative is `herdr_pane wait_output` with a **two-part freshness check** — a prompt-preceded-by-output match alone still cannot distinguish a completed silent command (`cd`, `export`, `set`: no output at all) from a stale pre-existing prompt:

1. **Before issuing the instruction**, `herdr_pane read` the pane and note the visible buffer's line count and last line.
2. **After the student reports done**, the step counts as complete only if BOTH hold: the buffer has **grown** past the snapshot (new lines exist below it) AND the final line matches the idle prompt. The growth requirement is the only disambiguator for silent commands.
3. Residual limit (accepted, not solvable from the pane alone): a long-running command that is still silent looks identical to "done, no output". For known-slow commands, wait on an expected output fragment instead of the prompt, or have the student run `echo step-N-done` as an explicit completion marker.

Still one blocking `wait_output` call per step, still no `bash sleep` polling. Never fall back to `sleep`+`read`: that is the noisy loop this section exists to avoid.

**Anti-patterns:**

- NEVER run the lesson's commands yourself and just show the student the transcript — they must type them.
- NEVER silently fix a mistake in their pane; narrate it so the correction is the lesson.
- NEVER end your turn after the gate instruction and re-prompt for the next gate — issue the gate in the same turn as the instruction so the student can answer it directly.
- NEVER `bash sleep` then `herdr_pane read` in a loop — every iteration is a streaming LLM reply, which is the exact failure mode this section is designed to prevent.
- NEVER busy-poll (`wait_output` with a zero/near-zero timeout in a tight retry loop) — use the push-UI question tool as the gate, or a single bounded `wait_output` if the gate is unavailable.
- NEVER gate on a bare idle-prompt regex (`$ `, `❯ `) — those matches exist in the visible buffer before the student types anything (stale-prompt false-positive), and output-anchored regexes fail on silent commands (`cd`, `export`). Require buffer growth past a pre-instruction snapshot **and** a trailing prompt match (see Fall-back above).
- NEVER narrate pane output as a correct result without first checking the read matches the step's expected command, with non-empty output where output is due (step b) — a confidently-wrong explanation is worse than no explanation.
- Fish-shell caveat from §1 applies to any snippet you dictate — flag `$status` vs `$?`, `set VAR val` vs `export`, etc. where the student's shell differs from what a bioinformatics tutorial usually assumes (bash).

## §7 Quiz / knowledge-check mode (human-driven pane)

**Course content intake.** §7 grades against the **Markdown-source / JSON-quiz** split:

- The lesson itself is plain Markdown — same path as §6 (`course-materials/<course>/<lesson>/{README,exercises}.md`).
- Quiz items live in `quiz.schema.v1.json` (sibling of `SKILL.md`) per item-kind vocabulary in §7's table.
- A new `quiz.import.sh --from <lesson-dir>` (or its agent equivalent) reads the lesson Markdown and emits a `quiz-N.json` matching `quiz.schema.v1.json`. The human or agent fact-checks every `correct` flag and `answer_key` before §7 sees it — never auto-grade from LLM-autogen, that is the authoritative-hallucination rule documented in `bin/quiz-import-pdf.py`'s docstring. When the lesson *itself* arrived via `--llm-stdin` (no parser handled the source), the `FILL_THIS.md` directive is what the agent reads on the next turn to author both the lesson Markdown and the quiz JSON against `source.txt`.
- Two `kind: task` items are also valid at the lesson→quiz boundary: a `task` item is *literally* the §6 gate, dressed with `task_id`, `instruction`, and the canonical 2-option gates.

§7's per-item loop below assumes the JSON is on disk; if it isn't, your first turn is "import the quiz from the lesson Markdown first."

Same side-pane setup as §6 (split with `focus: true` into a scratch dir; reuse the pane if one is already open — no new pane per quiz item). The difference is **output shape**: §6 is "do this and tell me when done," §7 is "answer this one question at a time." Same gate primitive (the host's push-UI question tool — see the *Host equivalents* table near the top of §6), different per-item loop.

Quiz item types map onto the tool's parameters as follows. Where features (preview, multiSelect, notes) are noted as "tool-forbidden", the §6 host-equivalents table explains which host provides them and which silently drops the field:

| Quiz item                              | Push-UI question shape                                                           | Notes                                                                                                                                                          |
| -------------------------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Single-answer MCQ (2–4 choices)        | 1 question, 2–4 options, `multiSelect: false`                                    | radio buttons; preview per option for code/data snippets (preview = Pi / rpiv only — see host table)                                                           |
| Multi-answer MCQ ("pick 2 of these 4") | 1 question, 2–4 options, `multiSelect: true`                                     | checkboxes; options[].preview forbidden by tool for multi-select (and unsupported on Claude Code / OpenCode)                                                   |
| Spot-the-bug / dry-run                 | 1 question, single-select, options each carry `preview: <markdown>`              | side-by-side compare ≥100 cols (Pi only); on Claude Code / OpenCode the preview string is silently ignored — narrate the bug in the option description instead |
| Short-answer recall                    | 1 question, 2 dummy options, prompt the student to use the `Type something.` row | free-text answer reaches the model verbatim (Pi only; Claude Code / OpenCode offer a similar free-text option in their native pickers)                         |
| Task ("actually run the command")      | reuse §6's 2-option gate (`I did it` / `Something went wrong`)                   | identical mechanism; here it counts as one quiz item with observable proof                                                                                     |

**Per-item loop** (one item = one push-UI question call, repeated until the quiz is exhausted — never batch more than one quiz item into a single call, because then per-item wrong-answer coaching has to wait until the whole batch resolves and the `Submit` review tab swallows intermediate feedback. On Claude Code / OpenCode, "one item per call" is even more strictly required because the host has no Submit review tab at all):

   a. Author the item. `header` ≤16 chars (e.g. `Q3 / 6: SAM flags`). Mark the correct option `(Recommended)` only if you're using it as the *default* choice during cold review — for graded items, do NOT mark correct; let the student earn it. The student can press Enter on a blank tab to reveal nothing; that's the right behavior for recall.
   b. The push-UI question tool — one blocking tool call. Agent emits zero tokens while the student answers. (See the *Host equivalents* table near the top of §6 for how each host renders this.)
   c. **On correct answer**: narrate the *why* (which property of the data triggered the right choice), then issue the next item in the same turn.
   d. **On wrong answer**: narrate the mistake before revealing the right answer ("the BAM index `.bai` is required because samtools random-access loads by `BAI` range, not the full file"). Use the `notes` field if the student added reasoning — it's on the answer envelope and reaches you as `user notes: <text>`.
   e. **On `Type something.` free text**: grade against the answer key you wrote (sometimes the student types a synonym or a longer form — accept obvious synonyms, narrate which forms you'd also accept).
   f. **On `Something went wrong` for task items**: §6 fall-back applies — read pane, diagnose, give corrected instruction, re-issue the same gate.

**End the loop** only when the quiz is exhausted. After the last item, emit one summary chat line with `score/total` and one short paragraph of *what to review before the next attempt* — pointers, not answers, so the student still has to do the next attempt themselves. Then `herdr_pane close` per the §1 hygiene rule.

**Anti-patterns:**

- NEVER batch 2+ quiz items into one push-UI question call — the `Submit` tab (Pi only) batches them but defers feedback until all are answered, which defeats per-item coaching. On Claude Code / OpenCode the same batching is even worse: the host has no review tab and answers in declaration order.
- NEVER mark the correct option `(Recommended)` on a graded MCQ — that hints at the answer and removes the recall value. `(Recommended)` belongs only on workflow gates like §6 ("just pressed Enter = happy path").
- NEVER use the `notes` field to smuggle the answer in — the student can read it; it's for *student → model* reasoning, not the reverse.
- NEVER run quiz commands in the agent's own pane — type them in the student pane only (§6 rule carries over).
- If the push-UI question tool is unavailable, the model has no equivalent fallback for graded MCQ (a `wait_output` regex can't capture a radio choice). In that host, end the quiz with a chat note and a `herdr_pane close` — do not invent a polling replacement.

**Interchange JSON (optional).** A quiz authored offline (PDF chapter → text → items by hand, lit-fetched paper, or a sibling skill like `study-designer`) can be dropped in as `quiz.schema.v1.json` (sibling of this file) and validated against `quiz.schema.v1.json` (JSON Schema 2020-12). §7 reads `items[]` one at a time and renders each via the per-item loop above; the `correct`, `answer_key`, and `gates` fields drive grading and §6 gate wiring. Inline-authored items skip the JSON entirely — the schema is a *convergence point* for importers, not a gate. `source.provenance` (PDF page, extractor toolchain) is preserved on each item so quizzes can be re-pointed at their facts during review.

---

Drift rule: if any section above starts restating tool parameters or capabilities, delete that section.
