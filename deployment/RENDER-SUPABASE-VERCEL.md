# 🚀 Deploy AI Sales CRM
## Render (Backend) + Supabase (DB) + Vercel (Frontend)
## Live at: crm.mindartdigital.com

---

## OVERVIEW

```
crm.mindartdigital.com  ──→  Vercel (Next.js frontend)
       │
       └─ /api/*  ──→  Render.com (FastAPI backend)
                             │
                             └─ Supabase (PostgreSQL DB)
```

Total cost on free tiers: **₹0/month** to start.

---

## STEP 1 — Supabase (Database) — 5 minutes

1. Go to **https://supabase.com** → Sign Up free
2. Click **"New Project"**
   - Name: `ai-sales-crm`
   - Password: (create a strong DB password — save it!)
   - Region: **Southeast Asia (Singapore)** — closest to India
3. Wait ~2 minutes for the project to be ready
4. Go to **Settings → Database** → copy the **Connection String (URI)**
   - It looks like: `postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres`
5. Go to **Settings → API** → copy:
   - **Project URL** (e.g. `https://xxxx.supabase.co`)
   - **anon public** key
   - **service_role** key (secret — keep safe)

✅ Save all these — you'll need them in Step 2.

---

## STEP 2 — Push Code to GitHub — 5 minutes

Render.com deploys from GitHub. You need to push your code there first.

1. Go to **https://github.com** → Sign up / Log in
2. Click **"New repository"** → name it `ai-sales-crm` → **Private** → Create
3. On your Windows PC open **Command Prompt** in `C:\Users\USER\claude-co-work\ai-sales-crm\`

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/ai-sales-crm.git
git push -u origin main
```

✅ All your files are now on GitHub.

---

## STEP 3 — Render.com (Backend API) — 10 minutes

1. Go to **https://render.com** → Sign up with GitHub
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo → select `ai-sales-crm`
4. Configure:
   - **Name**: `ai-sales-crm-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
   - **Region**: Singapore
5. Click **"Advanced"** → Add Environment Variables:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | (your Supabase connection string from Step 1) |
| `SECRET_KEY` | (any random 32-char string, e.g. `mysecretkey123abc456def789ghi012`) |
| `SUPABASE_URL` | (your Supabase project URL) |
| `SUPABASE_ANON_KEY` | (your Supabase anon key) |
| `AI_PROVIDER` | `openai` |
| `OPENAI_API_KEY` | (your OpenAI key — or leave blank to use keyword fallback) |
| `TWILIO_ACCOUNT_SID` | (your Twilio SID) |
| `TWILIO_AUTH_TOKEN` | (your Twilio token) |
| `TWILIO_WHATSAPP_FROM` | `whatsapp:+14155238886` |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USERNAME` | (your Gmail) |
| `SMTP_PASSWORD` | (your Gmail App Password) |
| `STRIPE_SECRET_KEY` | (your Stripe secret key) |
| `STRIPE_WEBHOOK_SECRET` | (fill after step 5) |
| `CORS_ORIGINS` | `https://crm.mindartdigital.com,http://localhost:3000` |

6. Click **"Create Web Service"**
7. Wait 3–5 minutes for deployment
8. You'll get a URL like: `https://ai-sales-crm-backend.onrender.com`
9. Test it: open `https://ai-sales-crm-backend.onrender.com/health` → should show `{"status":"ok"}`

### Create DB tables (one-time):
In Render → your service → **Shell** tab → run:
```bash
python create_tables.py
```

✅ Backend is live!

---

## STEP 4 — Vercel (Frontend) — 5 minutes

1. Go to **https://vercel.com** → Sign up with GitHub
2. Click **"Add New Project"** → Import `ai-sales-crm`
3. Configure:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend`
4. Add Environment Variables:
   - `NEXT_PUBLIC_API_URL` = `https://ai-sales-crm-backend.onrender.com`
   - `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` = `pk_live_your_key`
5. Click **"Deploy"**
6. Wait 2–3 minutes
7. You'll get a URL like: `https://ai-sales-crm.vercel.app`

✅ Frontend is live!

---

## STEP 5 — Point crm.mindartdigital.com to Vercel

1. In Vercel → your project → **Settings → Domains**
2. Click **"Add Domain"**
3. Type: `crm.mindartdigital.com`
4. Vercel will show you a DNS record to add

5. Go to wherever your domain DNS is managed (GoDaddy / Namecheap etc.)
6. Add a **CNAME record**:
   - Name: `crm`
   - Value: `cname.vercel-dns.com`
   - TTL: Auto

7. Wait 5–10 minutes → Vercel will auto-issue SSL

✅ **https://crm.mindartdigital.com** is now live!

---

## STEP 6 — Update Webhook URLs

Now update all your external service webhook URLs:

### Twilio WhatsApp:
Go to Twilio Console → WhatsApp Sandbox Settings:
```
Webhook URL: https://ai-sales-crm-backend.onrender.com/api/webhooks/whatsapp
```

### Facebook Lead Ads:
Go to Meta for Developers → Webhooks:
```
Callback URL: https://ai-sales-crm-backend.onrender.com/api/webhooks/facebook
Verify Token: (whatever you set in META_VERIFY_TOKEN env var)
```

### Stripe:
Go to Stripe Dashboard → Developers → Webhooks → Add endpoint:
```
URL: https://ai-sales-crm-backend.onrender.com/api/webhooks/stripe
Events: customer.subscription.created, customer.subscription.updated, customer.subscription.deleted
```
Copy the webhook signing secret → add to Render as `STRIPE_WEBHOOK_SECRET`

### Website Form:
```
https://ai-sales-crm-backend.onrender.com/api/webhooks/form/YOUR-WORKSPACE-SLUG
```

---

## STEP 7 — First Login

1. Open **https://crm.mindartdigital.com**
2. Click **"Create one free"** → Sign up
3. Go to **Automations** → Click **"Load Default Flows"**
4. You're ready to capture leads! 🎉

---

## Troubleshooting

**Backend sleeping (free tier)?**
Render free tier sleeps after 15 min inactivity. First request takes ~30 seconds to wake up.
Upgrade to paid ($7/mo) to keep it awake, or use UptimeRobot (free) to ping every 10 min:
- Go to https://uptimerobot.com → Add monitor → URL: `https://ai-sales-crm-backend.onrender.com/health`

**CORS errors in browser?**
Make sure `CORS_ORIGINS` in Render includes `https://crm.mindartdigital.com` exactly.

**Database connection failed?**
Double-check `DATABASE_URL` — the Supabase password must NOT contain special characters, or URL-encode them.

**Frontend shows blank page?**
Check Vercel deployment logs — usually a missing env variable or build error.

---

## Architecture Summary

```
User Browser
     │
     ▼
crm.mindartdigital.com (Vercel CDN — global, fast)
     │
     │  API calls → /api/*
     ▼
ai-sales-crm-backend.onrender.com (Render.com Singapore)
     │
     ├── Supabase PostgreSQL (database)
     ├── Ollama / OpenAI (AI analysis)
     ├── Twilio (WhatsApp messages)
     ├── SMTP Gmail (emails)
     └── Stripe (billing)
```

**Monthly cost on free tiers:**
- Vercel: Free (100GB bandwidth)
- Render: Free (sleeps after inactivity) or $7/mo (always on)
- Supabase: Free (500MB DB, 50K monthly active users)
- Total: ₹0 → ₹600/month
