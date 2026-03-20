<div align="center">

<img src="https://img.shields.io/badge/PRGuard-AI%20Code%20Quality%20Gate-00ff88?style=for-the-badge&logo=shield&logoColor=black" alt="PRGuard"/>

# 🛡️ PRGuard

### *Your code's last line of defense*

**AI-powered Pull Request reviewer that scores, comments, auto-fixes, and blocks bad code from reaching production.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-railway.app-7B2FBE?style=flat-square&logo=railway)](https://prguard-production-eae8.up.railway.app)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3-FF6B35?style=flat-square)](https://groq.com)
[![Railway](https://img.shields.io/badge/Deployed%20on-Railway-7B2FBE?style=flat-square&logo=railway)](https://railway.app)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

<br/>

![PRGuard Dashboard](https://img.shields.io/badge/Dashboard-Mission%20Control-00ff88?style=for-the-badge)

</div>

---

## ✨ What is PRGuard?

PRGuard is a GitHub bot that **automatically reviews every Pull Request** using LLaMA 3.3 running on Groq. It scores your code, posts inline comments on issues, creates auto-fix branches, and blocks bad code from merging — all within seconds of opening a PR.

No configuration required. Just install the webhook and it works.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🤖 **AI Code Review** | Scores every PR 0–10 across 8 quality categories |
| 💬 **Inline Comments** | Posts issues directly on the affected line in the diff |
| 🔥 **Auto-Fix Branch** | Creates a `prguard/fix-pr-*` branch with AI-applied corrections |
| 📊 **Team Dashboard** | Live dashboard tracking scores, trends, and pass rates across all repos |
| ⚙️ **Custom Rules** | Define team standards in `prguard.yml` — bot enforces them automatically |
| 💬 **PR Chat** | Comment `/prguard <question>` to ask the bot anything about the review |
| 🔄 **Smart Retry** | Handles API rate limits with exponential backoff (4 attempts) |
| ✅ **Commit Status** | Sets GitHub green ✅ or red ❌ check on every PR |

---

## 📸 Screenshots

### Team Dashboard
> Live metrics, score trends, issue categories, and review history

```
🛡️ PRGUARD  Mission Control                              ● ONLINE  01:12:35

// METRICS
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐
│  TOTAL REVIEWS  │ │   PASS RATE     │ │   AVG SCORE     │ │    REPOS    │
│      12         │ │     75%         │ │      7.2        │ │      3      │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────┘
```

### PR Review Comment
```
## ❌ PRGuard — Quality Gate FAILED

░░░░░░░░░░ 4.2 / 10

> Score 4.2/10 is below the threshold of 7/10.

### 📋 Verdict
Multiple high severity issues found. Naming violations and missing error handling.

### 🐛 Issues — 🔴 2 High · 🟡 2 Med · 🟢 1 Low

<details>
<summary>🔴 ⚠️ ERROR_HANDLING — `app/main.py` · L80</summary>
Problem: Missing try/except on network call...
Fix: Wrap in try/except httpx.HTTPStatusError...
</details>
```

---

## 🔍 Review Categories

PRGuard checks 8 categories on every PR:

```
🏷️  Naming        — Single letters, abbreviations, misleading names
🧩  Complexity    — Functions >30 lines, deeply nested conditionals
♻️  Duplication   — Repeated logic without abstraction
⚠️  Error Handling — Missing try/except on I/O, network, DB calls
🔢  Magic Values   — Hardcoded strings/numbers that should be config
🔐  Security       — Secrets in code, SQL injection, missing validation
🛡️  Type Safety    — Missing type hints in Python, implicit `any` in TS
💀  Dead Code      — Commented-out blocks, unused imports/variables
📋  Custom         — Your team's rules from prguard.yml
```

---

## ⚙️ Custom Rules (`prguard.yml`)

Add a `prguard.yml` file to your repo root to define team-specific standards:

```yaml
rules:
  - "All functions must have docstrings"
  - "No print() statements allowed in production code"
  - "All HTTP calls must have timeout set explicitly"
  - "Database calls must use transactions"
threshold: 8
```

PRGuard will enforce these rules on every PR in addition to the standard checks.

---

## 💬 PR Chat

Comment `/prguard <question>` on any PR to ask the bot anything:

```
/prguard what is the most critical issue to fix first?
/prguard how do I fix the complexity issue in main.py?
/prguard why did this PR fail the quality gate?
```

The bot will reply with a detailed, context-aware answer based on the review.

---

## 🏗️ Architecture

```
GitHub PR Event
      │
      ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Webhook   │────▶│  FastAPI App │────▶│  Groq API   │
│  (GitHub)   │     │  (Railway)   │     │ LLaMA 3.3   │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Inline   │ │ Auto-Fix │ │Dashboard │
        │ Comments │ │ Branch   │ │(Postgres)│
        └──────────┘ └──────────┘ └──────────┘
```

### File Structure

```
PRGuard/
├── app/
│   ├── main.py           # FastAPI app & webhook handler
│   ├── ai_reviewer.py    # Groq review + retry logic
│   ├── auto_fixer.py     # AI fix branch creator
│   ├── github_client.py  # GitHub API wrapper
│   ├── formatter.py      # PR comment formatting
│   ├── database.py       # PostgreSQL storage
│   ├── dashboard.html    # Mission Control UI
│   ├── home.html         # Landing page
│   ├── rules.py          # prguard.yml parser
│   ├── chat.py           # /prguard chat handler
│   ├── models.py         # Pydantic models
│   └── config.py         # Settings & env vars
├── prguard.yml           # Custom rules (example)
├── Procfile              # Railway start command
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- GitHub account
- [Groq API key](https://console.groq.com) (free)
- [ngrok](https://ngrok.com) for local development (or deploy to Railway)

### 1. Clone & Install

```bash
git clone https://github.com/AtharvaVavhal/PRGuard.git
cd PRGuard
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file:

```env
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
PASS_SCORE_THRESHOLD=7
LOG_LEVEL=INFO
DATABASE_URL=postgresql://...   # For PostgreSQL (Railway provides this)
```

### 3. Run Locally

```bash
uvicorn app.main:app --port 8000
```

### 4. Set Up GitHub Webhook

- Go to your repo → **Settings → Webhooks → Add webhook**
- **Payload URL:** `https://your-ngrok-url/webhook/github`
- **Content type:** `application/json`
- **Events:** Select `Pull requests` and `Issue comments`
- Add your webhook secret

### 5. Add Custom Rules (Optional)

Create `prguard.yml` in your repo root:

```yaml
rules:
  - "All functions must have docstrings"
  - "No hardcoded API keys"
threshold: 7
```

---

## ☁️ Deploy to Railway

1. Fork this repo
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub**
3. Add **PostgreSQL** database to your project
4. Set environment variables in the **Variables** tab
5. Railway auto-deploys on every push

Your public URL will be: `https://your-app.up.railway.app`

Update your GitHub webhook URL to point to Railway.

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| **API Framework** | FastAPI + Uvicorn |
| **AI Model** | LLaMA 3.3 70B via Groq |
| **GitHub Integration** | GitHub REST API v3 |
| **Database** | PostgreSQL (Railway) |
| **HTTP Client** | httpx |
| **Config Parsing** | PyYAML |
| **Deployment** | Railway |
| **Language** | Python 3.11 |

---

## 📊 How Scoring Works

| Score | Grade | Meaning |
|---|---|---|
| 9–10 | ⭐ Excellent | Near-perfect. Ready to merge. |
| 7–8  | ✅ Good | Acceptable for production. Minor issues only. |
| 5–6  | ⚠️ Borderline | Real problems that need fixing. |
| 3–4  | ❌ Poor | Multiple critical issues. Do not merge. |
| 0–2  | 🚨 Unacceptable | Rewrite required. |

Multiple HIGH severity issues cannot score above 6.

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request — PRGuard will review it automatically! 🤖

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ · Powered by **Groq + LLaMA 3.3** · Deployed on **Railway**

⭐ **Star this repo if PRGuard saved your codebase!**

[Live Demo](https://prguard-production-eae8.up.railway.app) · [Report Bug](https://github.com/AtharvaVavhal/PRGuard/issues) · [Request Feature](https://github.com/AtharvaVavhal/PRGuard/issues)

</div>