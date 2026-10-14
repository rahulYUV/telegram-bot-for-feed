# Argon Feed Bot

An asynchronous Telegram bot that monitors Instagram accounts for new reels and delivers them automatically, with support for on-demand media downloads via direct Instagram links.

---

## Features

- **Automated Feed Polling:** Checks tracked Instagram accounts every 12 hours for new posts/reels.
- **Deduplication:** Uses SQLite to store post IDs and prevent duplicate notifications.
- **On-Demand Downloads:** Send any public Instagram post or reel link (`/p/`, `/reel/`, `/reels/`, `/tv/`) to download and view the media directly in chat.
- **Per-Chat Subscriptions:** Individual users can manage their own target list.

---

## Project Structure

```text
argon-bot/
├── config.py       # API keys, tokens, and poll interval configuration
├── db.py           # SQLite async database schema and query helpers
├── fetcher.py      # RapidAPI Instagram scraper request handlers
├── main.py         # Telegram bot handlers and background job scheduler
└── requirements.txt
```

## Installation & Setup

### 1. Clone the repository & create environment

```bash
git clone <repository_url>
cd argon-bot
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

### 2. Install dependencies

### 3. Configure credentials

Update config.py with your credentials: