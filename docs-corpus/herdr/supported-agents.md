# Supported agents / harnesses in herdr (curated cross-reference)

> CURATED from herdr's own docs (`online-docs-0.8.2/agents.md`, `agent-skill.md`) and the
> verbatim `herdr agent start --help` kind enum (`../harnesses/herdr-supported-kinds.txt`).
> Docs snapshot 0.8.2 vs installed CLI 0.8.0 — re-capture the kind enum if a kind is rejected.

## Full cross-reference

| # | herdr kind (`agent start --kind`) | Docs name | State authority | Integration role |
|---|---|---|---|---|
| 1 | `pi` | Pi | lifecycle hooks if installed, else screen manifest | state + session |
| 2 | `claude` | Claude Code | screen manifest | session |
| 3 | `codex` | Codex | screen manifest | session |
| 4 | `gemini` | Gemini CLI | ⚠️ "detected but less thoroughly tested" | — |
| 5 | `cursor` | Cursor Agent CLI | screen manifest | session |
| 6 | `devin` | Devin CLI | screen manifest | session |
| 7 | `agy` | Antigravity CLI | screen manifest | session |
| 8 | `cline` | Cline | ⚠️ "detected but less thoroughly tested" | — |
| 9 | `omp` | OMP | lifecycle hooks when installed | state + session |
| 10 | `mastracode` | MastraCode | lifecycle hooks when installed | state + session |
| 11 | `opencode` | OpenCode | lifecycle plugin if installed, else screen manifest | state + session |
| 12 | `copilot` | GitHub Copilot CLI | screen manifest | session |
| 13 | `kimi` | Kimi Code CLI | lifecycle hooks if installed, else screen manifest | state + session |
| 14 | `kiro` | Kiro CLI | screen manifest | **none** |
| 15 | `droid` | Droid | screen manifest | session |
| 16 | `amp` | Amp | screen manifest | **none** |
| 17 | `grok` | Grok CLI | screen manifest | session |
| 18 | `hermes` | Hermes Agent | screen manifest | session |
| 19 | `kilo` | Kilo Code CLI | lifecycle plugin if installed, else screen manifest | state + session |
| 20 | `qodercli` | Qoder CLI | screen manifest | session |
| 21 | `maki` | Maki | screen manifest | **none** |
| — | *(no kind)* | Qwen Code | screen manifest (docs list it; kind enum has no `qwen`) | session |
| — | `gemini`, `cline` | — | see ⚠️ rows above | — |

## Detection & state rules that affect the skill's workflow

- **Lifecycle-authority agents** (pi, omp, mastracode, kimi, opencode, kilo with
  hooks/plugin installed): hook reports are the sole authority for `idle`/`working`/
  `blocked` — screen-manifest fallback is disabled to avoid two sources of truth.
- **Screen-manifest agents** (claude, codex, copilot, cursor, droid, agy, grok, …):
  state is classified from the live bottom-buffer screen snapshot via TOML manifests.
  Herdr checks herdr.dev for remote manifest updates automatically (disable with
  `[update] manifest_check = false`).
- **Blocked detection is deliberately strict**: only known approval/question/permission
  UI shapes mark `blocked`. Unknown prompts fall back to `idle` labelled
  `default_known_agent_idle_fallback` → **an unlearned prompt can settle as `idle`
  while the agent actually waits for input** — reinforces SKILL.md §2 (never treat a
  settled state as completion without reading output).
- **No-integration agents** (amp, kiro, maki): detection only; no session identity.
- **Gemini CLI and Cline**: detected but "less thoroughly tested" → expect more
  misclassifications; verify output extra carefully when delegating to them.
- **Qwen Code**: listed in docs but absent from the 0.8.0 `--kind` enum — may require a
  newer herdr binary to start via `herdr agent start`.

## Wrapper / environment gotchas

- Host-visible wrappers hide the real agent process. Set `HERDR_AGENT=<agent>` on the
  wrapper command, e.g. `HERDR_AGENT=claude fence -- claude` (Linux) or
  `HERDR_AGENT=claude nono run --profile claude-code -- claude` (macOS). Applies only
  to that foreground process; do NOT export globally.
- Local detection overrides: `~/.config/herdr/agent-detection/<agent>.toml` (local wins
  over remote/bundled; invalid files are ignored with a warning).
- Debug detection with `herdr agent explain --file screen.txt --agent codex --json`.
- Install integration hooks: `herdr integration install claude` (per-agent; gives
  lifecycle authority + session identity).

## Sources

- `online-docs-0.8.2/agents.md` §Supported agents, §Status authority
- `agent-skill.md` (same table, agent-skill view)
- `../harnesses/herdr-supported-kinds.txt` (verbatim `herdr agent start --help`, 0.8.0)