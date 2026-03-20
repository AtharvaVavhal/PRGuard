# PR Reviewer — AI-Powered GitHub Quality Gate

Analyzes pull request diffs, scores code quality (0–10), and blocks merges below threshold.

## Architecture

```
GitHub PR Event
      │
      ▼
POST /webhook/github          ← FastAPI (signature verified)
      │
      ├── get_pr_diff()       ← GitHub REST API (unified diff)
      │
      ├── review_pr()         ← OpenAI GPT-4o (structured JSON response)
      │
      ├── post_pr_comment()   ← GitHub Issues API (formatted markdown)
      │
      └── set_commit_status() ← GitHub Statuses API (pass/fail gate)
```

## Folder Structure

```
pr-reviewer/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app, webhook handler, orchestration
│   ├── config.py         # Settings from environment
│   ├── models.py         # Pydantic models (PRContext, ReviewResult, CodeIssue)
│   ├── github_client.py  # GitHub REST API: diff fetch, comment, status
│   ├── ai_reviewer.py    # OpenAI prompt + response parser + mock
│   └── formatter.py      # Markdown comment builder
├── test_local.py         # Local integration tests (no real tokens needed)
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

```bash
git clone <this-repo>
cd pr-reviewer

python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and fill in your tokens
```

## GitHub Token Permissions

Create a **fine-grained PAT** at https://github.com/settings/tokens with:
- `contents: read`
- `pull-requests: write`  ← for posting comments
- `commit-statuses: write`  ← for setting pass/fail status

## Run Locally

```bash
# With real OpenAI
uvicorn app.main:app --reload --port 8000

# With mock AI (no OpenAI key needed)
USE_MOCK_AI=true uvicorn app.main:app --reload --port 8000
```

Health check: http://localhost:8000/health

## Local Tests (no tokens needed)

```bash
USE_MOCK_AI=true python test_local.py
```

## End-to-End Testing with ngrok

### 1. Start your server
```bash
USE_MOCK_AI=true uvicorn app.main:app --port 8000
```

### 2. Expose it with ngrok
```bash
# Install: https://ngrok.com/download
ngrok http 8000
# Copy the https URL, e.g. https://abc123.ngrok-free.app
```

### 3. Configure GitHub Webhook
Go to: `https://github.com/<owner>/<repo>/settings/hooks/new`

| Field | Value |
|-------|-------|
| Payload URL | `https://abc123.ngrok-free.app/webhook/github` |
| Content type | `application/json` |
| Secret | Your `GITHUB_WEBHOOK_SECRET` value |
| Events | Select **"Pull requests"** only |

### 4. Open a PR
Create or update a PR in your repo. Within seconds you should see:
- A comment posted on the PR with the score and issues
- A status check (✅ or ❌) on the commit

### 5. Require the status check (enforce the gate)
Go to: `Settings → Branches → Branch protection rules → main`
- Enable: **"Require status checks to pass before merging"**
- Search for: `pr-reviewer/quality`
- Enable: **"Require branches to be up to date before merging"**

Now PRs with score < 7 literally cannot be merged.

## Tuning

| Config | Default | Description |
|--------|---------|-------------|
| `PASS_SCORE_THRESHOLD` | 7 | Minimum score to pass |
| `OPENAI_MODEL` | gpt-4o | Swap to gpt-4o-mini for lower cost |
| `USE_MOCK_AI` | false | Skip OpenAI for local testing |

## Adding More Review Categories

Edit the `SYSTEM_PROMPT` in `app/ai_reviewer.py`. Add entries to the `WHAT YOU MUST FLAG` section and the `category` enum in `models.py`.
