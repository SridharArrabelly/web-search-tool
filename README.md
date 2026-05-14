# web-search-tool

Sample scripts demonstrating web-search grounding for LLM agents using:

- **Azure AI Foundry** agents with the built-in `WebSearchTool` (Bing Web Search and Bing Custom Search)
- **Microsoft Agent Framework** agents wrapping the same Foundry tools (with optional Redis caching)
- **OpenAI Responses API** with the native `web_search` tool (and `allowed_domains` filtering)

The samples are oriented around grounding answers in South African Revenue Service (SARS) content (`www.sars.gov.za`), but can be retargeted to any site or Bing Custom Search instance.

## Repository layout

| Path | Description |
| --- | --- |
| [websearch-oai.py](websearch-oai.py) | Calls OpenAI Responses API directly with `web_search` tool, restricted to `www.sars.gov.za` via `allowed_domains`. Prints input/output token usage. |
| [af-foundryagent.py](af-foundryagent.py) | Microsoft Agent Framework sample backed by a Foundry agent. |
| [agent-framework/af-websearchtool-bing.py](agent-framework/af-websearchtool-bing.py) | Agent Framework + Foundry `WebSearchTool` (Bing Web Search). |
| [agent-framework/af-websearchtool-bing-redis.py](agent-framework/af-websearchtool-bing-redis.py) | Same as above, with Redis-based response caching. |
| [agent-framework/redis_viewer.py](agent-framework/redis_viewer.py) | Helper to inspect the Redis cache. |
| [bing-custom-preview/bingcustomsearch-tool-preview.py](bing-custom-preview/bingcustomsearch-tool-preview.py) | Preview of the Bing Custom Search grounding tool (connection name lookup). |
| [web-search-tool/websearchtool-bing.py](web-search-tool/websearchtool-bing.py) | Foundry agent using Bing Web Search grounding. |
| [web-search-tool/websearchtool-bingcustom.py](web-search-tool/websearchtool-bingcustom.py) | Foundry agent using Bing Custom Search grounding (ARM connection ID). |
| [web-search-tool/websearchtool-bingcustom-instructions.py](web-search-tool/websearchtool-bingcustom-instructions.py) | Same as above, with richer system instructions. |
| [pyproject.toml](pyproject.toml) | Project dependencies (managed with [uv](https://docs.astral.sh/uv/)). |
| [.env](.env) | Local configuration (not committed). |

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** package manager
- **Azure CLI** (`az`) for local credential sign-in
- An **Azure AI Foundry** project with:
  - A deployed chat model (e.g. `gpt-5.1`)
  - A **Grounding with Bing Search** connection, and/or a **Grounding with Bing Custom Search** connection + instance
- An **OpenAI API key** (only for [websearch-oai.py](websearch-oai.py))
- (Optional) A reachable **Redis** instance for the cached Agent Framework sample

## Setup

### 1. Clone and enter the repo

```powershell
git clone <repo-url>
cd web-search-tool
```

### 2. Install dependencies with uv

```powershell
uv sync
```

This creates a `.venv/` and installs everything from `pyproject.toml` / `uv.lock`. The project pins pre-release Agent Framework packages, which are allowed via `[tool.uv] prerelease = "allow"` in [pyproject.toml](pyproject.toml).

Activate the environment (optional — `uv run` works without it):

```powershell
.\.venv\Scripts\Activate.ps1
```

> If activation is blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`.

### 3. Sign in to Azure

The Foundry samples use `DefaultAzureCredential`, so any of the standard Azure credential sources work. The simplest is:

```powershell
az login
az account set --subscription <your-subscription-id>
```

Your signed-in identity needs the **Azure AI User** role (or equivalent) on the Foundry project.

### 4. Configure `.env`

Create a `.env` file in the repo root with the values for your Foundry project / Bing connections:

```dotenv
# Azure AI Foundry project endpoint
# Format: https://<resource>.services.ai.azure.com/api/projects/<project>
PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>

# Model deployment name in the Foundry project
MODEL=gpt-5.1

# Bing Custom Search — name-based (used by bingcustomsearch-tool-preview.py)
CUSTOM_SEARCH_CONNECTION_NAME=<connection-name>
CUSTOM_SEARCH_INSTANCE_NAME=<custom-search-instance-name>

# Bing Custom Search — full ARM ID (used by websearchtool-bingcustom*.py)
BING_CUSTOM_SEARCH_CONNECTION_ID=/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<resource>/projects/<project>/connections/<connection-name>
BING_CUSTOM_SEARCH_INSTANCE_NAME=<custom-search-instance-name>

# OpenAI direct (only for websearch-oai.py)
OPENAI_API_KEY=sk-...

# Optional: Application Insights for tracing
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...;IngestionEndpoint=...

# Optional: Redis (for agent-framework/af-websearchtool-bing-redis.py)
REDIS_URL=redis://localhost:6379
```

The connection ID and instance name come from your Foundry project's **Connected resources → Grounding with Bing Custom Search** entry.

## Run the samples

Use `uv run` (no activation needed) or `python` inside the activated venv.

### OpenAI Responses API + web search (token-usage demo)

```powershell
uv run python websearch-oai.py
```

Restricts results to `www.sars.gov.za` via `tools[0].filters.allowed_domains` and prints input / output / total token counts. To target a different site, edit the `allowed_domains` list (up to 20 domains).

### Foundry agent — Bing Web Search

```powershell
uv run python web-search-tool/websearchtool-bing.py
```

### Foundry agent — Bing Custom Search

```powershell
uv run python web-search-tool/websearchtool-bingcustom.py
# or with extended instructions
uv run python web-search-tool/websearchtool-bingcustom-instructions.py
```

### Agent Framework + Foundry web search

```powershell
uv run python agent-framework/af-websearchtool-bing.py
```

### Agent Framework with Redis caching

Start Redis (e.g. via Docker) then:

```powershell
uv run python agent-framework/af-websearchtool-bing-redis.py
uv run python agent-framework/redis_viewer.py   # inspect cached entries
```

## Troubleshooting

- **`DefaultAzureCredential` failures** — run `az login` again and confirm `az account show` returns the expected subscription.
- **`PermissionDenied` on the Foundry project** — your identity needs the *Azure AI User* role on the project resource.
- **Bing Custom Search returns empty results** — verify `BING_CUSTOM_SEARCH_INSTANCE_NAME` matches an instance defined in the Bing Custom Search portal, and that the instance includes the domains you expect.
- **`web_search` tool errors from OpenAI** — ensure your account has access to the Responses API web-search tool and the model you specify supports it.

## Security notes

Never commit `.env`, API keys, or connection strings. The `.gitignore` excludes `.env` and `.venv/` by default — keep it that way and rotate any key that has been pasted into a chat or shared screen.
