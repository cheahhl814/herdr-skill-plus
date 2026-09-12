# Related community plugins (source 3 — unreviewed marketplace)

Captured 2026-09-12 from https://herdr.dev/plugins/. **Provenance tier 3**: self-tagged
(GitHub topic `herdr-plugin`), unreviewed by Herdr, unreviewed by this skill. Descriptions
below are the authors' own marketing copy, not verified claims — evaluate before installing.
Installing a plugin runs third-party code (`herdr plugin install owner/repo`); this skill
only points at candidates, it never installs one on its own.

## §4 quota/model discovery

- **levi-qiao/herdr-agent-quota** — **installed and configured 2026-09-12, v1.5.4.**
  Verified end-to-end: `refresh --json`/`dashboard` are dead ends for `claude`/`agy` (they
  need pane/session context the raw binary doesn't have and just report `unavailable`,
  even with real data sitting on disk). The actual data source is passive: once
  `herdr plugin action invoke configure --plugin herdr-agent-quota` (not the raw binary —
  it refuses direct `configure --apply` and insists on running through Herdr) installs a
  statusLine hook into `~/.claude/settings.json` (verified: adds only a `statusLine` block,
  nothing else touched) / `~/.gemini/antigravity-cli/settings.json` for agy, the harness
  itself writes real quota on every turn to
  `~/.local/state/herdr/plugins/herdr-agent-quota/claude-statusline.observation.json` (and
  the `agy-statusline` equivalent) — confirmed with live data: 5h window 25% used, weekly
  7% used, 98% cache hit rate, read directly from that file rather than any subcommand.
  Coverage is narrower than the marketing copy implies: **no copilot, pi, or opencode
  support at all** (still use the scrape recipe there); `codex` only works with
  ChatGPT-subscription auth, not API-key auth. Enabling it is a standing-config change —
  ask the user first; Claude Code's self-modification guard blocks running `configure`
  as a self-edit, so hand it to the user to run in a pane. See SKILL.md §4 for the wired-in
  usage.
  `herdr plugin install levi-qiao/herdr-agent-quota`
- **uwuclxdy/clauth** — Claude Code multi-account manager + usage monitor (CLI/TUI/MCP),
  cross-account delegation. Relevant if spreading delegation across multiple Claude
  accounts to route around a hard cap (§4.6 refusals note still applies per-account).
  `herdr plugin install uwuclxdy/clauth`

## §2/§3 verification & detection-limit workarounds

- **arvemy/herdr-convo** — **installed 2026-09-12, v0.1.1.** Verified end-to-end: pure
  Node CLI (`node <plugin-root>/src/cli.ts`), no build step. `locate <pane_id>` correctly
  identified a live Claude Code session's own transcript file; `latest <pane_id> --text`
  returned that session's actual last turn verbatim, read from
  `~/.claude/projects/<cwd-slug>/<session>.jsonl` directly — not the terminal. A genuine
  fix for §2's alternate-screen truncation and pane-scraping generally. Covers **claude,
  codex, opencode, pi only** — does not help with gemini/cline/copilot/agy detection
  limits in §3, contrary to what the description alone suggests. `read <target> --cursor
  <C>` gives incremental turns for polling a long delegation without repeated full pane
  reads; error codes are clean JSON (`cursor_stale`, `session_not_found`,
  `no_agent_session`, `herdr_unavailable`, `unsupported_agent`) — fall back to
  `herdr_agent read` on any of them. See SKILL.md §2/§3 for the wired-in usage.
  `herdr plugin install arvemy/herdr-convo`
- **furkankly/zoetrope** — **installed 2026-09-12, v0.2.0.** Manifest is at
  `herdr-plugin/`, not the repo root — install as `furkankly/zoetrope/herdr-plugin`, a
  bare `furkankly/zoetrope` install fails immediately with an opaque OS error before any
  preview. Needs `herdr integration install claude` (and/or `codex`) first so Herdr can
  attribute sessions, and `herdr plugin action invoke setup-keys --plugin
  furkankly.zoetrope` after, which binds `prefix+shift+z` (backs up
  `~/.config/herdr/config.toml` first) — that binding opens a **human-facing** live
  flow-graph overlay on a focused agent pane; not something this skill drives
  programmatically. It does have a headless surface: `zoe inspect <session_id>`
  (claude/codex only, no pane-id support — get a session id from `herdr-convo locate`)
  printed a correct structured summary for this session (model, 90 tool calls
  82✓/7✗/1⏳) — a cheap stuck/erratic-state signal, cheaper than a full
  `herdr-convo latest --text` read. See SKILL.md §1 (user-facing visibility) and §2/§3
  (headless health check) for the wired-in usage.
  `herdr plugin install furkankly/zoetrope/herdr-plugin`
- **persiyanov/herdr-reviewr**, **smarzban/herdr-file-viewer**,
  **odiumuniverse/herdr-diff-viewer** — diff/file-viewer sidebars for inspecting what a
  delegated agent actually changed; useful for matching output against §2's explicit
  completion signal.

## Orchestration at scale

- **nelsonPires5/herdr-board** — **trialed 2026-09-12, v0.16.1, then uninstalled. BROKEN
  on this herdr version — do not reinstall for actual dispatch without re-checking first.**
  The manifest's own comment warns it targets
  exactly Herdr 0.8.2/protocol 20; this machine runs Herdr 0.9.0/protocol 22. Verified: a
  test card moved into an `auto` column queued, then failed immediately with
  `herdr protocol error [incompatible_protocol]: Herdr 0.8.2 with protocol 20 is required
  (found Herdr 0.9.0 with protocol 22)` — confirmed via `board daemon status --json`
  (`"herdr_connected": false`) before the dispatch attempt even happened. The card/column/
  comment CRUD layer (SQLite-backed, works standalone) is otherwise fine and fully
  scriptable (`board --json`), but the one feature this plugin exists for — spawning an
  agent into a live pane — cannot work until the plugin ships a protocol-22 update. Not
  wired into SKILL.md; re-check `board --version` / re-test dispatch after any plugin
  update before reconsidering.
- **dcolinmorgan/herdr-remote** — **installed 2026-09-12, v0.8.0, local-only mode (user's
  explicit choice — see below).** This is a bigger step than the other candidates: remote
  (phone/Telegram) access grants **full control**, not read-only monitoring — approve/block
  decisions, send commands, interrupt agents, "trust all tools for blocked agents" (a remote
  approval-gate bypass). Remote requires the user to separately stand up a Cloudflare Tunnel,
  a `HERDR_RELAY_TOKEN`, and (for Telegram) a bot token from `@BotFather` — credential setup
  this skill does not perform. **As installed here**: the herdr plugin manifest wires only one
  event hook (`pane.agent_status_changed` → `uv run relay/on_event.py`), which sends one UDP
  packet to `127.0.0.1:8376` and does nothing else — verified no process listens on that port
  and no relay/menu-bar/Telegram service is auto-started by the plugin install. To get actual
  local monitoring (menu bar/TUI, still loopback-only) the user must separately run
  `relay/start.sh` in the plugin directory — a standing background service, left to the user
  to start. Not wired into SKILL.md beyond this note: it doesn't change any workflow step,
  it's a parallel human-facing monitoring channel like zoetrope's overlay, not something an
  orchestrating agent calls.
  `herdr plugin install dcolinmorgan/herdr-remote`
- **0cv/herdr-mobile-relay** — not evaluated yet; same remote-control risk profile as
  herdr-remote likely applies (unverified) — confirm scope with the user before installing.

## Not fetched

Full marketplace has 1,101 plugins across 1,082 repos; this list covers what surfaced on
the "Trending"/"Popular" views on the capture date. Re-browse https://herdr.dev/plugins/
for anything more specific (e.g. a bioinformatics-specific pane tool) before assuming
nothing else fits.
