> ## Documentation Index
> Fetch the complete documentation index at: https://docs.ollama.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Oh My Pi

Oh My Pi (OMP) is a terminal coding agent with IDE-style tools built in. It combines chat, project context, structured code edits, language server support, debugging tools, browser access, plugins, and subagents in one terminal workflow.

Ollama can configure OMP to use Ollama as its model provider and launch an interactive session.

![Oh My Pi with Ollama](http://files.ollama.com/omp.png)

## Quick setup

```bash theme={"system"}
ollama launch omp
```

This configures Ollama as a provider, sets up web search tools, and starts OMP.

### Run directly with a model

```shell theme={"system"}
ollama launch omp --model <model>
```

## Plugins

OMP supports plugins for extra tools and capabilities. When launching OMP through Ollama, the Ollama web search plugin is managed automatically.

## Manual setup

Install OMP from [omp.sh](https://omp.sh), then run:

```bash theme={"system"}
ollama launch omp --config
```
