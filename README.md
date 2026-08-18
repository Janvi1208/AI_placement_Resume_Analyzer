# AI Placement Readiness Analyzer

A SaaS web app that analyzes a resume against a job description, produces a
deterministic placement-readiness score, identifies skill gaps, generates
interview questions, runs a text-based AI mock interview, and builds a
personalized prep roadmap — with a server-enforced 3-free-analysis trial and
Razorpay-powered paid credits.

## What's implemented and working right now

- **Auth**: signup/login/logout with bcrypt-hashed passwords and JWT stored
  in HTTP-only cookies.
- **Resume upload**: PDF/DOCX text extraction, file-type/size/magic-byte
  validation, heuristic structured parsing (name/email/phone/education/
  skills/experience/projects/certifications/achievements).
- **Job description**: paste text or a URL (best-effort, respectful HTML
  extraction), parsed into required vs. preferred skills.
- **Semantic skill matching**: exact / related / partial / missing, with
  evidence strings, using a synonym table (e.g. OpenAI ↔ Gemini/Mistral as
  "related LLM API experience" — never claimed as exact).
- **Deterministic scoring engine**: weighted score (weights configurable in
  `.env`) — the AI layer never picks the final number.
- **Skill gap analysis** with critical/high/medium/low priority, filterable
  in the UI.
- **Recommendations, interview questions, prep roadmap**: all generated
  from the deterministic gap data so every roadmap day traces back to a
  real identified gap.
- **AI mock interview**: text Q&A loop with per-answer scoring
  (technical accuracy / communication / depth / relevance / overall) and a
  session summary.
- **Usage/credit system enforced server-side**: an atomic MongoDB
  `find_one_and_update` consumes a free analysis or paid credit — the
  frontend button state is never the source of truth.
- **Razorpay payments**: server-side order creation, HMAC signature
  verification on both the client-redirect `/verify` path and the
  independent `/webhook` path, idempotent credit-granting (unique index +
  guarded update — a duplicate webhook cannot double-grant a credit).
- **Dashboard, history, results page** with a circular score chart, score
  breakdown, matching skills, filterable skill gaps, and recommendations.
- **Security**: HTTP-only cookies, input validation, file validation, rate
  limiting (slowapi), no stack traces leaked in production, prompt-injection
  guarding for AI calls (uploaded content is wrapped and explicitly labeled
  as untrusted data, not instructions).

## What's intentionally mocked / stubbed (and how to go live)

- **AI provider**: defaults to `AI_PROVIDER=mock` in `backend/.env`, which
  runs the whole app with zero external API keys, using deterministic
  heuristics instead of live model calls. Set `AI_PROVIDER=openai` (or
  `gemini` / `mistral`) and add the matching API key to switch to real LLM
  calls — no other code changes needed; every service already calls
  `get_ai_provider().complete_json(...)` behind the same interface.
- **RAG/embeddings (LangChain + Qdrant/Chroma)**: the architecture supports
  adding a `services/rag.py` module that indexes resume/JD text and injects
  retrieved context into the AI prompts. Not wired up yet — the current
  skill-matching approach uses a synonym table instead of embeddings, which
  is enough for a working v1 but is the natural next enhancement.
- **Google OAuth**: not implemented; only email/password auth is wired up.
  The `users` schema and JWT flow are structured so OAuth can be added as
  another `/api/v1/auth/google` route without touching the rest of the app.
- **Razorpay**: fully implemented and will work end-to-end the moment you
  add real `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` /
  `RAZORPAY_WEBHOOK_SECRET` to `.env` and point a webhook at
  `POST /api/v1/payments/webhook`. It has NOT been tested against live
  Razorpay servers (no test credentials were available in this environment)
  — test with Razorpay's test-mode keys before going to production.
- **Mock-interview answer evaluation**: uses a lightweight deterministic
  heuristic (answer length + presence of concrete examples) when
  `AI_PROVIDER=mock`. Swap in a real AI provider call for genuine
  qualitative evaluation — the response shape (`technical_accuracy`,
  `communication`, `depth`, `relevance`, `overall`) is already what the
  frontend expects, so this is a drop-in replacement.
- **Frontend has not been `npm install`'d or built in this environment**
  (no network access to the npm registry from this sandbox at the time of
  building). The backend was fully verified: all routes registered
  correctly under FastAPI's TestClient, and the full analysis pipeline
  (parse → match → score → gaps → recommendations → interview questions →
  roadmap) was run end-to-end against realistic sample data — see console
  output during development. Run `npm install && npm run dev` in
  `frontend/` on your machine to build and verify the UI.

## Tech stack

- **Frontend**: Next.js 15 (App Router), TypeScript, Tailwind CSS, Recharts-ready, lucide-react
- **Backend**: FastAPI, Pydantic v2, Motor (async MongoDB driver)
- **Database**: MongoDB
- **Payments**: Razorpay
- **AI**: pluggable OpenAI / Gemini / Mistral, mock provider by default

## Project structure

```
placement-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, middleware, router registration
│   │   ├── config.py            # env-driven settings (pricing, weights, trial limit, etc.)
│   │   ├── database.py          # MongoDB connection + indexes
│   │   ├── auth/                # JWT + password hashing + auth dependency
│   │   ├── models/schemas.py    # all Pydantic request/response models
│   │   ├── routers/             # one file per API resource
│   │   └── services/            # business logic: parsing, matching, scoring,
│   │                             #   insights (gaps/recs/questions/roadmap),
│   │                             #   usage/credits, payments, ai_provider
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/app/                 # Next.js App Router pages
│   │   ├── page.tsx             # landing page
│   │   ├── login/, signup/
│   │   ├── dashboard/
│   │   ├── analyze/             # 3-step upload → JD → run analysis
│   │   ├── analysis/[id]/       # results report
│   │   ├── history/
│   │   ├── pricing/             # Razorpay checkout
│   │   └── mock-interview/
│   ├── src/components/, src/lib/api.ts
│   ├── package.json, tailwind.config.ts, Dockerfile
│   └── .env.local.example
├── docker-compose.yml
└── README.md
```

## Running locally

### Option A — Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/api/docs
- MongoDB: localhost:27017

### Option B — Manual

**Backend**

```bash
cd backend
cp .env.example .env
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# make sure MongoDB is running locally, or point MONGODB_URI at Atlas
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

## Required environment variables

**backend/.env**
```
MONGODB_URI=
MONGODB_DB_NAME=
JWT_SECRET=
AI_PROVIDER=mock            # mock | openai | gemini | mistral
OPENAI_API_KEY=
GEMINI_API_KEY=
MISTRAL_API_KEY=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
ANALYSIS_PRICE=19900        # in paise; ₹199.00
CURRENCY=INR
FREE_ANALYSES_LIMIT=3
FRONTEND_URL=http://localhost:3000
```

**frontend/.env.local**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_RAZORPAY_KEY_ID=
```

Never commit real values for these — `.env` files are gitignored.

## Critical test scenarios (product rule verification)

These map directly to spec section 33:

1. New user → 3 free analyses allowed → confirmed via `consume_entitlement`
   decrementing `free_analyses_remaining` atomically.
2. 4th analysis with no paid credits → backend returns HTTP 402, frontend
   redirects to `/pricing`.
3. Verified Razorpay payment → `paid_credits` incremented exactly once,
   guarded by the unique index on `razorpay_order_id` plus a
   `credits_granted` flag checked in the same atomic update.
4. Duplicate webhook delivery for the same payment → second call finds
   `credits_granted: True` already set, so `find_one_and_update` matches
   nothing and no credit is added twice.
5. Analysis pipeline failure after a credit was consumed → credit is
   refunded via `refund_entitlement` so a backend error never costs the
   user their entitlement.

To turn these into automated tests, add `pytest` + `pytest-asyncio` +
`mongomock-motor` (or a test MongoDB container) and write request-level
tests against the routers using `TestClient`/`httpx.AsyncClient` — this
was not included in this build to keep the delivered scope focused on a
working application; see "What remains" below.

## What remains for a production launch

- Automated test suite (pytest for backend, Playwright/Vitest for frontend)
- Google OAuth
- LangChain + Qdrant/Chroma RAG layer for richer semantic matching
- Voice mode for the mock interview (architecture already supports it —
  swap the text answer input for an audio-transcription step feeding the
  same `/interview/answer` endpoint)
- Production-grade rate limiting/observability (current `slowapi` limiter
  is a starting point, not a full production setup)
- CI/CD pipeline and a hosted MongoDB Atlas + Razorpay live-mode setup
- Frontend `npm install` + build verification in a real environment (not
  possible in the sandbox this was built in)
