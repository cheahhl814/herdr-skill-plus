# Providers & task-tier matrix (curated)

> CURATED summary. Wiring recipes verified against `ollama-online-docs/` (ingested
> 2026-09-02, Ollama 0.30.0) and each harness's own docs. Model NAMES here are examples
> seen on this machine — always re-discover live (SKILL.md §4.6). Never cite quotas or
> prices from this file.

## Harness × provider capability matrix

| Harness | Native provider(s) | Alternate-provider mechanism | Ollama wiring |
|---|---|---|---|
| pi | anthropic, ollama, google (default google) | `--provider <name>` launch flag | `pi --provider ollama --model <id>` |
| opencode | 75+ providers | config (`opencode.json` providers) | `ollama launch opencode`; 23 ollama models listed via `opencode models` |
| claude | Anthropic-locked | Anthropic-compatible API via Ollama | `ollama launch claude` (0.30+) |
| codex | OpenAI (ChatGPT/API) | `model_providers` in config.toml | `ollama launch codex` (refreshes catalog) |
| copilot | GitHub-hosted models | env: `COPILOT_PROVIDER_TYPE=openai` (any OpenAI-compatible endpoint incl. Ollama/vLLM), `COPILOT_PROVIDER_API_KEY` (not needed for local Ollama), base-URL var | ollama-online-docs/copilot-cli.md has full env table |
| gemini CLI | Google-locked | none | not supported |
| agy | Google-locked | none | not supported |
| droid | Factory | ollama launch supported | `ollama launch droid --config` |
| cline, hermes, omp, kimi, others | see ollama-online-docs/integrations/ | varies | check per-integration page; not all herdr kinds have recipes |

`ollama launch <app>` (Ollama ≥0.30) interactively wires a harness to Ollama models —
supported: OpenCode, Claude Code, Codex, VS Code, Droid (+ `--model`, `--yes`, `--config`
flags). When launched this way, Ollama refreshes the harness's model catalog automatically.

## Ollama specifics

- **`:cloud` suffix** = runs on Ollama's cloud service (requires `ollama signin` on
  ollama.com account); same CLI surface as local models. No local GPU needed.
- **Local models**: run on-box (GPU/CPU); fully offline/private; need VRAM headroom.
- **Pre-flight**: `ollama list` to confirm the model exists; `ollama pull <model>` is a
  prerequisite (not implicit); local inference requires the ollama daemon running
  (`ollama serve` / system service — check with `ollama ps`).
- **Auth caveat (2026-09-02 battle test)**: a model appearing in a harness's model list
  does NOT mean it is usable — opencode's `ollama-cloud/<a-listed-cloud-model>` was listed but the
  provider returned `Unauthorized` at first prompt (opencode's ollama-cloud provider needs
  its own auth/API key setup). Treat model listing ≠ model usable; if the first prompt
  fails with an auth error, fall back to the next property-matched candidate (see
  SKILL.md §3).
- **Trade-off property**: local-small = fast/cheap/private but weaker at heavy agentic
  work; cloud models = large-model capability without local GPU, but egress + account
  dependency.
- **Privacy use-case**: offline/no-egress work is a legitimate reason to force
  local-only models — ask the user when the task might involve sensitive data.

## Task-tier matching (heuristics — match discovered options by PROPERTY, not by name)

| Tier | Task shape | Required properties | Example mapping |
|---|---|---|---|
| **T0** trivial/bulk | lint fixes, mechanical renames, doc formatting, batch small edits | cheap, fast, tool-use adequate | harness default model; opencode+ollama cloud-small; pi on local model |
| **T1** standard dev | single/few-file features, bugfixes, tests | solid tool-use reliability, mid context | harness native default (claude/codex/pi/opencode defaults) |
| **T2** heavy agentic | multi-file refactor, cross-cutting changes, long planning | large context, strongest reasoning + tool-use, cost-insensitive OK | claude/codex top models; pi large-context provider model; avoid local-small |
| **T3** read-only/review | code review, analysis, research, quota probes | read-only mode (pair with §4.5 plan/read-only flags) | cheaper models acceptable; gemini `--approval-mode plan`, claude `--permission-mode plan` |

Decision procedure at runtime:
1. Classify the task into a tier (T0–T3).
2. Discover what's actually available: harness list → provider list per harness →
   model list per provider (§4 commands; `ollama list` for Ollama).
3. Match discovered options against the tier's required properties — never against a
   remembered model name.
4. If multiple options qualify: prefer the user's established preference (their
   subscription/native defaults), then cheaper, then faster.
5. State the chosen tier + option in one line before launching.

## Refusals & cautions

- **Never sum or infer shared quota** across harnesses that proxy the same provider
  account — quota probes are harness-local only.
- **Verify the ACTIVE provider before trusting a quota probe or cost estimate** —
  provider wiring (config.toml, env vars, opencode.json) can silently point a harness
  at a different backend than assumed.
- **API keys/base-URLs for custom providers** go through §5 discipline: never typed by
  the agent into chat, never echoed; set via env/config the user edits.
- **Don't switch a harness's provider config** without asking the user — it changes
  billing and data residency.
- **Don't hardcode model names or quota numbers** in prompts/plans — they rot (drift rule).

## Sources

- `ollama-online-docs/` — cloud.md, cli.md (`ollama launch`), integrations per harness (claude-code, codex, opencode, copilot-cli, pi, droid, cline, hermes, oh-my-pi)
- `../harnesses/copilot-online-docs/about-copilot-cli.md` §Using your own model provider
- Machine facts verified 2026-09-02: ollama 0.30.0, `pi --list-models` providers (anthropic, ollama), `opencode models` ollama count