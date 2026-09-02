# Permission / auto-approval flags per harness (curated)

> CURATED summary derived from the verbatim captures in this directory (captured
> 2026-09-02). If a flag fails, re-read the harness's `help-<harness>.md` and
> re-capture — flags drift between CLI versions. Pass these to
> `herdr_agent start` via `agentArgs`.

## Summary table

| Harness | Full auto-approval (yolo) | Intermediate (edits auto, exec asks) | Read-only / plan | Notes |
|---|---|---|---|---|
| claude | `--dangerously-skip-permissions` or `--permission-mode bypassPermissions` | `--permission-mode acceptEdits` | `--permission-mode plan` | choices: acceptEdits, auto, bypassPermissions, manual, dontAsk, plan |
| codex | `--dangerously-bypass-approvals-and-sandbox` | `-s workspace-write` + `-a never` (or `--approve-for-me` for auto-reviewed approvals) | `-s read-only` | sandbox `-s`: read-only, workspace-write, danger-full-access; approval `-a`: untrusted, on-request, never. NOTE: no `--full-auto` flag in this version — verify against help-codex.md before citing |
| gemini | `-y` / `--yolo` or `--approval-mode yolo` | `--approval-mode auto_edit` | `--approval-mode plan` ⚠ | approval modes: default, auto_edit, yolo, plan. ⚠ 2026-09-02 battle test: installed gemini-cli rejects `--approval-mode plan` at startup with "available when experimental.plan is enabled" — the plan mode is gated behind an `experimental.plan` config setting in newer CLIs; re-verify with `gemini --help` before relying on it, or use yolo/auto_edit with a read-only prompt |
| copilot | `--allow-all` (= allow-all-tools + paths + urls) | `--allow-all-tools` (paths/urls still asked) | — | granular: `--allow-tool`, `--allow-all-paths`, `--allow-all-urls`, `--add-dir` |
| agy | `--dangerously-skip-permissions` | — | — | single switch, auto-approves all tool requests |
| pi | none needed | none needed | — | no permission popups by design; executes directly; `--approve`/`-a` trusts project-local files |
| opencode | none surfaced in `--help` | none surfaced in `--help` | — | permissions are config-driven (`opencode.json` `permission` settings), not CLI flags |

## Guidance

- **Default for delegated helper work**: intermediate mode (edits auto-approved, shell
  commands still gated) — enough autonomy without full yolo. Full yolo only when the
  user explicitly asks, or the task is in a throwaway sandbox/cwd.
- **Read-only review work**: plan/read-only modes (`claude --permission-mode plan`,
  `codex -s read-only`, `gemini --approval-mode plan`) — pairs well with the quota probe.
- **Trust-dialog interaction still applies**: even with auto-approval flags, first run
  in a new folder can show the workspace trust dialog (see SKILL.md §3) — that dialog
  is outside the permission-mode system.
- **opencode exception**: if opencode blocks on permissions, fix it via its config file,
  not CLI flags. Ask the user before editing permission config.

## Escalation ladder (when an agent is blocked on approval in-pane)

1. Read the pane to classify the prompt (§3 of SKILL.md).
2. Single approval → send the confirmation key(s) (cursor usually on "Yes"/accept).
3. Repeated approvals for the same kind of action → note it; for future starts of this
   harness, pass the intermediate auto-approval flag via `agentArgs`.
4. Never answer approval prompts that ask for secrets or credentials — escalate to user.