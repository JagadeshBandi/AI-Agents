# TapApply

Autonomous global job application platform. Upload your CV (or build one from scratch) and let TapApply apply to jobs across 10 regions 24/7 — tracking every application, preparing you for interviews, and staying compliant with robots.txt at every step.

---

## Architecture

```
tapapply/
├── backend/          # FastAPI service (Python 3.11+)
│   ├── app.py        # Main application, all routes
│   ├── Dockerfile
│   └── src/
│       ├── automation/    # Playwright stealth browser engine
│       ├── compliance/    # GDPR transience layer (temp file reaper)
│       ├── intelligence/  # ATS CV builder, job scraper (150 sample jobs)
│       └── support/       # WebSocket support agent + connection hub
├── frontend/         # Next.js 16 (App Router) + Tailwind CSS
│   ├── src/app/
│   │   ├── onboarding/    # 3-step wizard (region → sector → profile)
│   │   ├── dashboard/     # Autopilot toggle + SSE log console
│   │   ├── track/         # Application ledger with pipeline view
│   │   └── interview/[id] # STAR-framework interview simulator
│   ├── src/components/
│   │   ├── FloatingGuide.tsx  # 24/7 support agent (7-sec stall detection)
│   │   └── AppNav.tsx
│   └── src/lib/
│       ├── api.ts     # Fully typed API client
│       └── ws.ts      # WebSocket client with auto-reconnect
├── chrome_extension/ # Browser extension (companion)
├── docker-compose.yml
├── .env.example
└── LICENSE
```

---

## Features

| Feature | Detail |
|---|---|
| **Flexible onboarding** | Path A: CV upload (PDF/DOCX); Path B: manual profile builder that generates an ATS-optimised CV without any upload |
| **10 regions** | UK, USA, Canada, Australia, New Zealand, Germany, France, Netherlands, Ireland, Spain |
| **5 sectors** | Technology, Finance, Healthcare, Marketing, Engineering |
| **Autopilot engine** | 8-second async cycle — scans, applies, updates tracking automatically |
| **Stealth automation** | Humanised typing (50–180 ms/char), non-linear scroll, randomised click delays, `navigator.webdriver` override, robots.txt compliance |
| **GDPR transience** | CV files wiped from disk as soon as the submission loop closes; background TTL reaper runs every 60 s |
| **Support agent** | WebSocket-powered, 7-second stall detection triggers field-specific suggestions; auto-reconnects at 5 s |
| **Interview simulator** | STAR-framework mock questions, company intel, culture signals — fully template-based, no LLM required |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Playwright Chromium (`playwright install chromium`)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

### Docker (full stack)

```bash
cp .env.example .env   # fill in your values
docker compose up --build
```

Services:

| Service | Port |
|---|---|
| Frontend | 3000 |
| Backend API | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

---

## Environment Variables

Copy `.env.example` to `.env` and set:

```
DATABASE_URL=sqlite:///./tapapply.db   # or postgresql://...
SECRET_KEY=change-me
PROXY_URL=                             # optional residential proxy
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/onboarding/step1` | Set region |
| `POST` | `/api/onboarding/step2` | Set sector |
| `POST` | `/api/onboarding/step3/upload` | Upload CV (PDF/DOCX) |
| `POST` | `/api/onboarding/step3/manual` | Manual profile → ATS CV |
| `GET` | `/api/profile/{user_id}` | Fetch profile |
| `GET` | `/api/jobs/{user_id}` | Available job listings |
| `GET` | `/api/applications/{user_id}` | All applications |
| `PATCH` | `/api/applications/{id}/status` | Update application status |
| `GET` | `/api/interview/{application_id}` | Interview prep session |
| `POST` | `/api/autopilot/enable` | Start autopilot |
| `POST` | `/api/autopilot/disable` | Stop autopilot |
| `GET` | `/api/logs/stream` | SSE event stream (log + stats) |
| `WS` | `/ws/support/{client_id}` | Support agent WebSocket |

---

## License

MIT
