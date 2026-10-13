# Approval Engine - Django Assessment

Please finish **Setup** before your interview so we can start straight away.

## Setup

You only need [uv](https://docs.astral.sh/uv/). It brings the right Python with it.

**1. Install uv** (skip if `uv --version` works)

macOS / Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Then open a **new** terminal.

**2. Clone and check**

```bash
git clone https://github.com/ghanshyam-plateIq/approval-engine-interview.git
cd approval-engine-interview
uv run dev.py check
```

It should end with **All set**. If not, send the output to your interviewer.

**No local setup?** On GitHub click **Code -> Codespaces -> Create codespace**, wait for it to
build, then run `uv run dev.py check` in its terminal.

## During the interview

```bash
uv run dev.py                       # starts Django on http://localhost:8000
uv run interview/run.py <code>      # your interviewer gives you codes
```

A **start code** writes the next task into `problem/`. A **check code** runs automated checks
against your code (no need to have the server running for those).

Use any editor and the tools you normally use. Talk through your thinking as you go.

## Everyday commands

Run these from `backend/`:

| Task | Command |
|---|---|
| Make / apply migrations | `uv run manage.py makemigrations approvals` then `uv run manage.py migrate` |
| Load the seed data | `uv run manage.py load_seed` |
| Django shell | `uv run manage.py shell` |
| Your own tests | `uv run manage.py test approvals` |

To start from an empty database: stop the server, delete `backend/db.sqlite3`, run `uv run dev.py`.

## Layout

```
backend/            Django project
  approvals/        the app you'll build (models, views, urls, load_seed command)
  config/           settings and root urls
  seed.json         sample users, policies and invoices
interview/          code runner (don't edit) and locked task data
dev.py              setup check and server runner
```
