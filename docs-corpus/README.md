# docs-corpus — offline documentation snapshots for the herdr skill

Offline Markdown snapshots of upstream docs so agents consult real flags instead of
hallucinating them. Regenerate captures rather than hand-editing them.

Two provenance tiers per file:
- **Source 1 — verbatim CLI captures** (`help-*.md`, `status.md`): authoritative for the pinned installed version. Note: absolute `$HOME` paths that leaked the local username in two captures (`help-root.md`, `status.md`) were genericized to `$HOME/...` on 2026-09-02 for public publish — otherwise verbatim.
- **Source 2 — online docs** (`*-online-docs/`, `online-docs-*/`, upstream repo copies): richer context (concepts, config files, quotas, permission semantics) ingested via docs-ingest from official sites/repos; may be newer or older than the installed binary.
- **Source 3 — community marketplace** (`herdr/related-plugins.md`): self-tagged, unreviewed third-party plugins from herdr.dev/plugins/. Candidates only — never installed automatically, evaluate before use.

## Layout

```
docs-corpus/
├── README.md               this index
├── herdr/                  herdr CLI + pi-herdr plugin
│   ├── help-root.md … help-workspace.md, status.md   verbatim CLI captures (source 1)
│   ├── online-docs-0.8.2/  20 English .mdx pages from github.com/ogulcancelik/herdr
│   │                       docs/versions/0.8.2 (concepts, cli-reference, agents,
│   │                       agent-automation, agent-skill, troubleshooting,
│   │                       config-reference, plugins, integrations, …)
│   ├── upstream-skill-SKILL.md   herdr's own shipped agent skill (upstream reference)
│   ├── agent-guide.md      distribution/agent-guide.md (setup + diagnosis recipes)
│   ├── github-README.md    repo README
│   ├── plugin-README.md, plugin-index.ts   pi-herdr plugin (tool-level docs + source)
│   └── related-plugins.md  CURATED, source 3: community-marketplace plugin candidates
│                           for §2-§4 gaps (quota API, transcript normalization, dispatch)
└── harnesses/              supported coding-agent CLIs installed on this machine
    ├── permission-modes.md         CURATED summary: auto-approval/yolo flags per harness
    ├── herdr-supported-kinds.txt   verbatim `herdr agent start --help` kind list
    ├── help-<harness>.md           verbatim `--help` captures (source 1) × 7
    ├── claude-online-docs/        code.claude.com .md: permissions, permission-modes,
    │                              cli-reference, model-config, settings
    ├── codex-online-docs/         github.com/openai/codex docs/: config, sandbox,
    │                              authentication, getting-started, agents_md, exec,
    │                              skills, slash_commands
    ├── gemini-online-docs/        github.com/google-gemini/gemini-cli docs/: cli-reference,
    │                              model, model-routing, plan-mode, sandbox, checkpointing,
    │                              quota-and-pricing, troubleshooting
    ├── opencode-online-docs/      opencode.ai/docs .md: permissions, cli, models,
    │                              config, agents
    ├── pi-online-docs/            github.com/badlogic/pi-mono coding-agent docs/: usage,
    │                              models, providers, sessions, session-format, skills,
    │                              extensions, environment-variables + READMEs
    ├── agy-online-docs/           antigravity.google/docs .md: cli overview/using/
    │                              features/headless, models, permissions
    └── copilot-online-docs/       docs.github.com .md: allowing-tools, configure,
                                   cli-programmatic-reference, cli-command-reference,
                                   about-copilot-cli
└── providers/              alternative-model-provider corpus (Ollama etc.)
    ├── ollama-online-docs/  docs.ollama.com .md: cloud, cli, faq, context-length,
    │                        troubleshooting + integrations for claude-code, codex,
    │                        opencode, copilot-cli, pi, droid, cline, hermes, oh-my-pi
    └── providers-matrix.md  CURATED: harness×provider wiring, Ollama :cloud vs local,
                             T0–T3 task-tier matching, refusals (facts behind §4.6)
```

Captured 2026-09-02: herdr 0.8.0 (docs snapshot 0.8.2), Claude Code 2.1.258, codex/opencode/pi/gemini/agy/copilot as installed. Verify the version in each harness's `help-<harness>.md` header before trusting flag details.

## Ingestion methods used (docs-ingest decision tree)

| Tool | Strategy | Endpoint |
|---|---|---|
| herdr | GitHub repo clone → extract docs/ + skills/ + distribution/ | github.com/ogulcancelik/herdr |
| claude | Static docs site, raw-markdown endpoint | code.claude.com/docs/en/<page>.md |
| codex | GitHub repo clone → docs/*.md | github.com/openai/codex |
| gemini | GitHub repo clone → docs/**.md | github.com/google-gemini/gemini-cli |
| opencode | Sitemap + raw-markdown endpoint | opencode.ai/docs/<page>.md |
| pi | GitHub repo clone → packages/coding-agent/docs/ | github.com/badlogic/pi-mono |
| agy | llms.txt index + raw-markdown endpoint | antigravity.google/docs/<page>.md |
| copilot | Web search to locate pages + .md endpoint | docs.github.com/en/copilot/…/<page>.md |

## Regenerating

```bash
# Source 1: herdr CLI captures
cd docs-corpus/herdr
for c in "--help" "agent --help" "agent start --help" "agent prompt --help" \
         "pane --help" "pane run --help" "workspace --help"; do
  herdr $c > "help-$(echo $c | tr ' ' '-').md"
done
# Source 1: harnesses — re-run the cap() loop; each file header stamps date + command.
# Source 2: re-clone the repos / re-curl the .md endpoints listed above.
```

## Reading order for an agent debugging a herdr/harness failure

1. `harnesses/permission-modes.md` — is this a blocked-on-approval case?
2. `harnesses/help-<harness>.md` — exact flags for that harness (model, permission, sandbox).
3. `harnesses/<harness>-online-docs/` — deeper semantics: permission config files, quotas,
   sandbox policies, slash commands (source 2; may differ from installed version).
4. `herdr/help-agent*.md`, `herdr/help-pane*.md` — exact herdr subcommand semantics.
5. `herdr/online-docs-0.8.2/` — herdr concepts, config reference, troubleshooting.
6. `herdr/plugin-README.md` — tool-level contracts (alternate screen, truncation, stalled prompts).