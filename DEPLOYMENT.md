# AI Sales CRM — Complete Deployment Guide

## Stack
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL (Supabase)
- **Frontend**: Next.js 14 + Tailwind CSS
- **AI**: Ollama (local LLM — llama3)
- **WhatsApp**: Twilio
- **Billing**: Stripe
- **DB**: Supabase (managed PostgreSQL)

---

## 1. Prerequisites

```bash
# Required
- Python 3.11+
- Node.js 20+
- Docker (optional)
- Ollama installed locally

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3  # Download the AI model (~4GB)
```

---

## 2. Database Setup (Supabase)

1. Go to [supabase.com](https://supabase.com) → New Project
2. Copy your **Connection String** (Settings → Database)
3. Copy your **API URL** and **Service Role Key**
4. Paste into `.env` file

---

## 3. Environment Configuration

```bash
# Backend
cd backend
cp ../.env.example .env
# Edit .env with your real credentials
```

**Required API Keys:**
| Variable | Where to Get |
|---|---|
| `DATABASE_URL` | Supabase → Settings → Database |
| `SUPABASE_URL` | Supabase → Settings → API |
| `TWILIO_ACCOUNT_SID` | [twilio.com/console](https://twilio.com/console) |
| `TWILIO_AUTH_TOKEN` | [twilio.com/console](https://twilio.com/console) |
| `TWILIO_WHATSAPP_FROM` | Twilio WhatsApp Sandbox number |
| `SMTP_USERNAME` | Your Gmail address |
| `SMTP_PASSWORD` | Gmail App Password (not regular password) |
| `META_ACCESS_TOKEN` | Meta for Developers → Graph API Explorer |
| `META_VERIFY_TOKEN` | Any random string you choose |
| `STRIPE_SECRET_KEY` | [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys) |
| `STRIPE_WEBHOOK_SECRET` | Stripe → Webhooks → Your endpoint |

---

## 4. Backend Setup & Run

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create database tables
python create_tables.py

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs available at: **http://localhost:8000/docs**

---

## 5. Frontend Setup & Run

```bash
cd frontend

# Copy env
cp .env.local.example .env.local
# Edit NEXT_PUBLIC_API_URL if backend is not on localhost:8000

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend available at: **http://localhost:3000**

---

## 6. WhatsApp (Twilio) Setup

1. Create Twilio account → Get sandbox number
2. In Twilio Console → WhatsApp Sandbox:
   - Set webhook URL: `https://your-domain.com/api/webhooks/whatsapp`
   - Method: POST
3. Test by sending `join <your-sandbox-code>` to the Twilio number

---

## 7. Facebook Lead Ads Setup

1. Go to [Meta for Developers](https://developers.facebook.com)
2. Create App → Add Webhooks product
3. Configure webhook:
   - URL: `https://your-domain.com/api/webhooks/facebook`
   - Verify Token: (same as `META_VERIFY_TOKEN` in .env)
4. Subscribe to `leadgen` field
5. Create Lead Ads form and note the **Form ID**
6. Create a Campaign in the CRM and enter the Facebook Form ID

---

## 8. Stripe Billing Setup

1. Create products in Stripe Dashboard:
   - Pro plan: ₹999/month
   - Agency plan: ₹2999/month
2. Copy **Price IDs** to `.env` (`STRIPE_PRO_PRICE_ID`, `STRIPE_AGENCY_PRICE_ID`)
3. Create webhook in Stripe → Developers → Webhooks:
   - URL: `https://your-domain.com/api/webhooks/stripe`
   - Events: `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`
4. Copy webhook signing secret to `STRIPE_WEBHOOK_SECRET`

---

## 9. Website Form Integration

Embed this form on any website:

```html
<form id="crm-form">
  <input name="name" placeholder="Name" required />
  <input name="email" type="email" placeholder="Email" />
  <input name="phone" placeholder="Phone" />
  <textarea name="message" placeholder="Message"></textarea>
  <button type="submit">Submit</button>
</form>

<script>
document.getElementById('crm-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  await fetch('https://your-api.com/api/webhooks/form/YOUR-WORKSPACE-SLUG', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  alert('Thank you! We will be in touch.');
});
</script>
```

---

## 10. Docker Deployment

```bash
# Build and run everything
docker-compose up --build -d

# Check logs
docker-compose logs -f backend

# Pull Ollama model inside container
docker exec crm_ollama ollama pull llama3
```

---

## 11. Production Deployment

### Backend → Railway / Render

```bash
# Railway
npm install -g @railway/cli
railway login
railway init
railway up
```

### Frontend → Vercel

```bash
npm install -g vercel
vercel --prod
# Set NEXT_PUBLIC_API_URL to your Railway backend URL
```

### Database → Supabase (already managed)

---

## 12. Default Automations

After setup, visit **Automations** page and click **"Load Default Flows"** to activate:

| Flow | Trigger | Action |
|---|---|---|
| Instant Hot Lead Reply | Score > 70 | Send WhatsApp AI reply |
| 24h Follow-up | No reply in 24h | Send follow-up email |
| Price Inquiry | Keyword: "price" | Send pricing WhatsApp |
| 48h Final Follow-up | No reply in 48h | Send final WhatsApp |

---

## 13. API Documentation

Full interactive API docs: `http://localhost:8000/docs`

Key endpoints:
```
POST /api/auth/signup          — Register
POST /api/auth/login           — Login
GET  /api/leads                — List leads (with filters)
POST /api/leads                — Create lead
GET  /api/analytics/dashboard  — Dashboard metrics
GET  /api/analytics/ai-insights — AI insights
POST /api/webhooks/whatsapp    — Twilio webhook
POST /api/webhooks/facebook    — Meta webhook
POST /api/webhooks/form/{slug} — Website form
POST /api/webhooks/stripe      — Stripe webhook
WS   /ws/{workspace_id}        — Real-time notifications
```

---

## Project Structure

```
ai-sales-crm/
├── backend/
│   ├── main.py              ← FastAPI app entry point
│   ├── database.py          ← SQLAlchemy setup
│   ├── requirements.txt
│   ├── create_tables.py     ← Run once to create DB tables
│   ├── core/
│   │   ├── config.py        ← All settings from .env
│   │   └── security.py      ← JWT utilities
│   ├── models/              ← SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── workspace.py
│   │   ├── lead.py
│   │   ├── campaign.py
│   │   ├── automation.py
│   │   ├── conversation.py
│   │   └── subscription.py
│   ├── api/routes/          ← FastAPI route handlers
│   │   ├── auth.py
│   │   ├── leads.py
│   │   ├── campaigns.py
│   │   ├── automations.py
│   │   ├── conversations.py
│   │   ├── analytics.py
│   │   ├── billing.py
│   │   └── webhooks.py      ← Twilio, Facebook, Stripe, Form
│   ├── services/            ← Business logic
│   │   ├── ai_service.py    ← Ollama AI integration
│   │   ├── whatsapp_service.py ← Twilio WhatsApp
│   │   ├── email_service.py ← SMTP email
│   │   ├── automation_engine.py ← Rule-based triggers
│   │   └── stripe_service.py ← Billing
│   └── workers/
│       └── follow_up_worker.py ← APScheduler background jobs
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx         ← Redirects to dashboard or login
│   │   ├── auth/
│   │   │   ├── login/page.tsx
│   │   │   └── signup/page.tsx
│   │   └── (dashboard)/    ← Protected routes
│   │       ├── layout.tsx   ← Auth guard + WebSocket
│   │       ├── dashboard/page.tsx
│   │       ├── leads/page.tsx
│   │       ├── campaigns/page.tsx
│   │       ├── automations/page.tsx
│   │       ├── chat/page.tsx
│   │       └── billing/page.tsx
│   ├── components/layout/
│   │   ├── Sidebar.tsx
│   │   └── Header.tsx
│   └── lib/
│       ├── api.ts           ← Axios API client
│       ├── auth.ts          ← JWT token helpers
│       └── types.ts         ← TypeScript interfaces
│
├── .env.example             ← Environment template
├── docker-compose.yml       ← Full stack Docker setup
└── DEPLOYMENT.md            ← This file
```
