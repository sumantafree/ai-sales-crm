# cPanel Deployment Guide
## crm.yourdomain.com → AI Sales CRM

---

## STEP 1 — Create the Subdomain in cPanel

1. Log in to **cPanel**
2. Go to **Domains** → **Subdomains**
3. Create:
   - Subdomain: `crm`
   - Domain: `yourdomain.com`
   - Document Root: `public_html/crm` (or leave default)
4. Click **Create**

---

## STEP 2 — Enable SSL (Free)

1. In cPanel go to **SSL/TLS** → **Let's Encrypt SSL**
2. Find `crm.yourdomain.com` and click **Issue**
3. Wait 1–2 minutes for SSL to activate
4. Your site will now be accessible at `https://crm.yourdomain.com`

---

## STEP 3 — Upload Project Files via SSH

Connect to your server via SSH (you can find SSH credentials in cPanel → SSH Access):

```bash
ssh username@yourdomain.com
```

Then upload and set up the project:

```bash
# Go to home directory
cd ~

# Upload your project (from your Windows PC use FileZilla or WinSCP)
# OR clone from GitHub if you pushed it there:
# git clone https://github.com/yourusername/ai-sales-crm.git

# Your folder structure should look like:
# ~/ai-sales-crm/
#   ├── backend/
#   └── frontend/
```

---

## STEP 4 — Set Up Python (Backend)

```bash
# Check Python version (needs 3.11+)
python3 --version

# Create virtual environment
cd ~/ai-sales-crm/backend
python3 -m venv ~/virtualenv/ai-sales-crm

# Activate it
source ~/virtualenv/ai-sales-crm/bin/activate

# Install all packages
pip install -r requirements.txt

# Copy and fill in your environment variables
cp ../../.env.example .env
nano .env    # Fill in DATABASE_URL, Twilio keys, Stripe keys etc.

# Create database tables (run once)
python create_tables.py
```

---

## STEP 5 — Set Up Node.js (Frontend)

### Option A: cPanel Node.js Selector (Recommended for cPanel)

1. In cPanel go to **Software** → **Setup Node.js App**
2. Click **Create Application**:
   - Node.js version: **20**
   - Application mode: **Production**
   - Application root: `ai-sales-crm/frontend`
   - Application URL: `crm.yourdomain.com`
   - Application startup file: `server.js`
3. Click **Create**
4. In the Node.js app, click **Run NPM Install**
5. Then in SSH:

```bash
cd ~/ai-sales-crm/frontend

# Create .env.local
echo "NEXT_PUBLIC_API_URL=https://crm.yourdomain.com" > .env.local
echo "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_your_key" >> .env.local

# Build the app
npm run build
```

### Option B: Manual via SSH

```bash
cd ~/ai-sales-crm/frontend
npm install
echo "NEXT_PUBLIC_API_URL=https://crm.yourdomain.com" > .env.local
npm run build
```

---

## STEP 6 — Configure .htaccess

Copy the `.htaccess` file from `deployment/cpanel/.htaccess` into your subdomain's document root:

```bash
cp ~/ai-sales-crm/deployment/cpanel/.htaccess ~/public_html/crm/.htaccess
```

This tells Apache to:
- Route `/api/*` requests → FastAPI backend on port **8000**
- Route everything else → Next.js frontend on port **3000**

> **Note:** Make sure `mod_proxy` and `mod_rewrite` are enabled.
> In WHM go to: **Service Configuration** → **Apache Configuration** → **Global Configuration**
> Check that `mod_proxy`, `mod_proxy_http`, `mod_proxy_wstunnel` are enabled.

---

## STEP 7 — Start Both Services

Make the scripts executable and run them:

```bash
chmod +x ~/ai-sales-crm/deployment/cpanel/*.sh

# Start backend (FastAPI on port 8000)
bash ~/ai-sales-crm/deployment/cpanel/start-backend.sh

# Start frontend (Next.js on port 3000)
bash ~/ai-sales-crm/deployment/cpanel/start-frontend.sh
```

Check logs:
```bash
tail -f ~/logs/crm-backend.log
tail -f ~/logs/crm-frontend.log
```

---

## STEP 8 — Auto-Restart on Reboot (Cron Job)

In cPanel go to **Cron Jobs** and add:

```
@reboot bash /home/USERNAME/ai-sales-crm/deployment/cpanel/start-backend.sh
@reboot bash /home/USERNAME/ai-sales-crm/deployment/cpanel/start-frontend.sh
```

Replace `USERNAME` with your actual cPanel username.

---

## STEP 9 — Test Everything

Visit these URLs to confirm everything works:

| URL | Expected |
|-----|----------|
| `https://crm.yourdomain.com` | Login page |
| `https://crm.yourdomain.com/api/health` | `{"status":"ok"}` |
| `https://crm.yourdomain.com/docs` | FastAPI Swagger docs |

---

## STEP 10 — Set Up Webhooks

Update all webhook URLs in your third-party services:

| Service | Webhook URL |
|---------|-------------|
| **Twilio WhatsApp** | `https://crm.yourdomain.com/api/webhooks/whatsapp` |
| **Facebook Lead Ads** | `https://crm.yourdomain.com/api/webhooks/facebook` |
| **Stripe** | `https://crm.yourdomain.com/api/webhooks/stripe` |
| **Website Form** | `https://crm.yourdomain.com/api/webhooks/form/YOUR-WORKSPACE-SLUG` |

---

## Troubleshooting

**Backend not starting?**
```bash
tail -50 ~/logs/crm-backend.log
# Check if port 8000 is available:
netstat -tlnp | grep 8000
```

**Frontend not loading?**
```bash
tail -50 ~/logs/crm-frontend.log
# Make sure build succeeded:
ls ~/ai-sales-crm/frontend/.next/
```

**502 Bad Gateway?**
- Backend or frontend process crashed — re-run the start scripts
- Check if mod_proxy is enabled in WHM

**Database connection error?**
```bash
cd ~/ai-sales-crm/backend
source ~/virtualenv/ai-sales-crm/bin/activate
python -c "from database import engine; print('DB OK')"
```

**Stop everything:**
```bash
bash ~/ai-sales-crm/deployment/cpanel/stop-all.sh
```

---

## File Transfer (Windows → Server)

Use **FileZilla** (free):
1. Download FileZilla from https://filezilla-project.org
2. Host: `ftp.yourdomain.com` or your server IP
3. Port: `21` (FTP) or `22` (SFTP — more secure)
4. Upload the entire `ai-sales-crm/` folder to `~/` on the server

Or use **WinSCP** — drag and drop from Windows Explorer to your server.
