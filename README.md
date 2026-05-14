# web-search-tool

Sample scripts demonstrating web-search grounding for LLM agents using:

- **Azure AI Foundry** agents with the built-in `WebSearchTool` (Bing Web Search and Bing Custom Search)
- **Microsoft Agent Framework** agents wrapping the same Foundry tools (with optional Redis caching)
- **OpenAI Responses API** with the native `web_search` tool (and `allowed_domains` filtering)

The samples are oriented around grounding answers in South African Revenue Service (SARS) content (`www.sars.gov.za`), but can be retargeted to any site or Bing Custom Search instance.

## Repository layout

```
web-search-tool/
├── README.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
└── samples/
    ├── agent_framework/
    │   ├── bing.py            # Agent Framework + Foundry WebSearchTool (Bing)
    │   └── bing_redis.py      # Same, with Redis response caching
    ├── foundry_sdk/
    │   ├── bing.py            # Foundry agent using Bing Web Search grounding
    │   └── bing_custom.py     # Foundry agent using Bing Custom Search grounding
    └── openai/
        └── responses_web_search.py  # OpenAI Responses API + web_search tool
```

| Path | Description |
| --- | --- |
| [samples/agent_framework/bing.py](samples/agent_framework/bing.py) | Agent Framework agent backed by the Foundry `WebSearchTool` (Bing Web Search). |
| [samples/agent_framework/bing_redis.py](samples/agent_framework/bing_redis.py) | Same as above, with Redis-based response caching. |
| [samples/foundry_sdk/bing.py](samples/foundry_sdk/bing.py) | Foundry agent using Bing Web Search grounding. |
| [samples/foundry_sdk/bing_custom.py](samples/foundry_sdk/bing_custom.py) | Foundry agent using Bing Custom Search grounding (ARM connection ID). |
| [samples/openai/responses_web_search.py](samples/openai/responses_web_search.py) | Calls OpenAI Responses API directly with the `web_search` tool, restricted via `allowed_domains`. Prints token usage. |
| [pyproject.toml](pyproject.toml) | Project dependencies (managed with [uv](https://docs.astral.sh/uv/)). |
| [.env.example](.env.example) | Template for local configuration; copy to `.env` (gitignored). |

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** package manager
- **Azure CLI** (`az`) for local credential sign-in
- An **Azure AI Foundry** project with:
  - A deployed chat model (e.g. `gpt-5.1`)
  - A **Grounding with Bing Search** connection, and/or a **Grounding with Bing Custom Search** connection + instance
- An **OpenAI API key** (only for [samples/openai/responses_web_search.py](samples/openai/responses_web_search.py))
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

Copy the template and fill in your values:

```powershell
Copy-Item .env.example .env
```

The connection ID and instance name come from your Foundry project''s **Connected resources → Grounding with Bing Custom Search** entry.

## Run the samples

Use `uv run` (no activation needed) or `python` inside the activated venv.

### OpenAI Responses API + web search (token-usage demo)

```powershell
uv run python samples/openai/responses_web_search.py
```

Restricts results to `www.sars.gov.za` via `tools[0].filters.allowed_domains` and prints input / output / total token counts. To target a different site, edit the `allowed_domains` list (up to 20 domains).

### Foundry agent — Bing Web Search

```powershell
uv run python samples/foundry_sdk/bing.py
```

### Foundry agent — Bing Custom Search

```powershell
uv run python samples/foundry_sdk/bing_custom.py
```

### Agent Framework + Foundry web search

```powershell
uv run python samples/agent_framework/bing.py
```

### Agent Framework with Redis caching

Start Redis (e.g. via Docker) then:

```powershell
uv run python samples/agent_framework/bing_redis.py
```

## Troubleshooting

- **`DefaultAzureCredential` failures** — run `az login` again and confirm `az account show` returns the expected subscription.
- **`PermissionDenied` on the Foundry project** — your identity needs the *Azure AI User* role on the project resource.
- **Bing Custom Search returns empty results** — verify `BING_CUSTOM_SEARCH_INSTANCE_NAME` matches an instance defined in the Bing Custom Search portal, and that the instance includes the domains you expect.
- **`web_search` tool errors from OpenAI** — ensure your account has access to the Responses API web-search tool and the model you specify supports it.

## Security notes

Never commit `.env`, API keys, or connection strings. The `.gitignore` excludes `.env` and `.venv/` by default — keep it that way and rotate any key that has been pasted into a chat or shared screen.
