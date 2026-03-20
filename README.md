<div align="center">

<br/>

# 🛡️ PRGuard

### *Your code's last line of defense*

**AI-powered Pull Request reviewer that scores, comments, auto-fixes, and blocks bad code from reaching production.**

<br/>

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Visit%20App-00ff88?style=for-the-badge&logoColor=black)](https://prguard-production-eae8.up.railway.app)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/Groq-LLaMA%203.3-FF6B35?style=for-the-badge)](https://groq.com)
[![Railway](https://img.shields.io/badge/Railway-Deployed-7B2FBE?style=for-the-badge&logo=railway)](https://railway.app)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)

<br/>

</div>

---

## 📖 What is PRGuard?

PRGuard is a GitHub bot that **automatically reviews every Pull Request** using LLaMA 3.3 running on Groq. It scores your code 0–10, posts inline comments on problem lines, creates auto-fix branches with AI-applied corrections, and sets a green ✅ or red ❌ commit status — all within seconds of opening a PR.

No configuration required. Just add the webhook and it works.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Code Review** | Scores every PR 0–10 across 8 quality categories |
| 💬 **Inline Comments** | Posts issues directly on the affected line in the diff |
| 🔥 **Auto-Fix Branch** | Creates a `prguard/fix-pr-*` branch with AI-applied corrections |
| 📊 **Team Dashboard** | Live dashboard with score trends, pass rates, and issue breakdown |
| ⚙️ **Custom Rules** | Define team standards in `prguard.yml` — bot enforces them automatically |
| 💬 **PR Chat** | Comment `/prguard <question>` to ask the bot anything about the review |
| 🔄 **Smart Retry** | Handles API rate limits with exponential backoff (4 attempts) |
| ✅ **Commit Status** | Sets GitHub green ✅ or red ❌ check on every PR |

---

## 🔍 Review Categories

PRGuard checks **8 categories** on every PR — plus any custom rules you define:

| Category | What It Checks |
|---|---|
| 🏷️ **Naming** | Single letters, abbreviations, misleading variable names |
| 🧩 **Complexity** | Functions >30 lines, deeply nested conditionals |
| ♻️ **Duplication** | Repeated logic blocks without abstraction |
| ⚠️ **Error Handling** | Missing try/except on I/O, network, and DB calls |
| 🔢 **Magic Values** | Hardcoded strings/numbers that should be constants or config |
| 🔐 **Security** | Secrets in code, SQL injection, missing input validation |
| 🛡️ **Type Safety** | Missing type hints in Python, implicit `any` in TypeScript |
| 💀 **Dead Code** | Commented-out blocks, unused imports and variables |
| 📋 **Custom** | Your team's own rules from `prguard.yml` |

---

## 📊 Scoring System

| Score | Grade | Meaning |
|---|---|---|
| 9–10 | ⭐ Excellent | Near-perfect. Ready to merge. |
| 7–8 | ✅ Good | Acceptable. Minor issues only. |
| 5–6 | ⚠️ Borderline | Real problems. Fix before merging. |
| 3–4 | ❌ Poor | Multiple critical issues. Do not merge. |
| 0–2 | 🚨 Unacceptable | Rewrite required. |

> Multiple HIGH severity issues cannot score above 6.

---

## ⚙️ Custom Rules (`prguard.yml`)

Drop a `prguard.yml` file in your repo root to enforce team-specific standards:

```yaml
rules:
  - "All functions must have docstrings"
  - "No print() statements allowed in production code"
  - "All HTTP calls must have timeout set explicitly"
  - "Database calls must use transactions"
threshold: 8
```

PRGuard picks this up automatically on every PR — no restarts needed.

---

## 💬 PR Chat

Comment `/prguard <question>` directly on any PR:

```
/prguard what is the most critical issue to fix first?
/prguard how do I fix the complexity issue in main.py?
/prguard why did this PR fail?
```

The bot replies with a detailed, context-aware answer based on the actual review results.

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
        │  Inline  │ │ Auto-Fix │ │Dashboard │
        │ Comments │ │  Branch  │ │(Postgres)│
        └──────────┘ └──────────┘ └──────────┘
```

### Project Structure

```
PRGuard/
├── app/
│   ├── main.py           # FastAPI app & webhook handler
│   ├── ai_reviewer.py    # Groq review engine + retry logic
│   ├── auto_fixer.py     # Auto-fix branch creator
│   ├── github_client.py  # GitHub API wrapper
│   ├── formatter.py      # PR comment formatting
│   ├── database.py       # PostgreSQL storage
│   ├── dashboard.html    # Mission Control UI
│   ├── home.html         # Landing page
│   ├── rules.py          # prguard.yml parser
│   ├── chat.py           # /prguard chat handler
│   ├── models.py         # Pydantic models
│   └── config.py         # Settings & env vars
├── prguard.yml           # Custom rules example
├── Procfile              # Railway start command
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- GitHub account & personal access token
- [Groq API key](https://console.groq.com) (free tier available)
- [ngrok](https://ngrok.com) for local development

### 1. Clone & Install

```bash
git clone https://github.com/AtharvaVavhal/PRGuard.git
cd PRGuard
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
PASS_SCORE_THRESHOLD=7
LOG_LEVEL=INFO
DATABASE_URL=postgresql://...        # Railway provides this automatically
```

### 3. Run Locally

```bash
# Start ngrok tunnel
ngrok http 8000

# Start the server
uvicorn app.main:app --port 8000
```

### 4. Set Up GitHub Webhook

1. Go to your repo → **Settings → Webhooks → Add webhook**
2. **Payload URL:** `https://your-ngrok-url/webhook/github`
3. **Content type:** `application/json`
4. **Secret:** your webhook secret
5. **Events:** select `Pull requests` and `Issue comments`

### 5. Add Custom Rules (Optional)

```yaml
# prguard.yml — place in your repo root
rules:
  - "All functions must have docstrings"
  - "No hardcoded API keys"
threshold: 7
```

---

## ☁️ Deploy to Railway

```bash
# 1. Fork this repo on GitHub

# 2. Go to railway.app → New Project → Deploy from GitHub repo
# 3. Add PostgreSQL database to the project
# 4. Set all environment variables in the Variables tab
# 5. Railway auto-deploys on every push ✅
```

Update your GitHub webhook URL to `https://your-app.up.railway.app/webhook/github`.

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| **API Framework** | FastAPI + Uvicorn |
| **AI Model** | LLaMA 3.3 70B via Groq |
| **GitHub Integration** | GitHub REST API v3 |
| **Database** | PostgreSQL |
| **HTTP Client** | httpx |
| **Config Parsing** | PyYAML |
| **Deployment** | Railway |
| **Language** | Python 3.11 |

---

## 🤝 Contributing

Contributions are welcome!

```bash
# 1. Fork the repo
# 2. Create your feature branch
git checkout -b feature/my-feature

# 3. Commit your changes
git commit -m 'add my feature'

# 4. Push and open a PR
git push origin feature/my-feature
```

> PRGuard will automatically review your PR. Meta. 🤖

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ &nbsp;·&nbsp; Powered by **Groq + LLaMA 3.3** &nbsp;·&nbsp; Deployed on **Railway**

<br/>

⭐ **Star this repo if PRGuard saved your codebase!**

<br/>

[🌐 Live Demo](https://prguard-production-eae8.up.railway.app) &nbsp;·&nbsp; [🐛 Report Bug](https://github.com/AtharvaVavhal/PRGuard/issues) &nbsp;·&nbsp; [💡 Request Feature](https://github.com/AtharvaVavhal/PRGuard/issues)

</div>
