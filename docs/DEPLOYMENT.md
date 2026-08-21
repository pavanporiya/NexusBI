# NexusBI Free Deployment Guide

Deploy NexusBI to production for $0/month using free-tier services.

## Architecture

```
Internet → Vercel (Frontend) → Railway (Backend API)
                                    ↓
                              Supabase (PostgreSQL)
                              Upstash (Redis)
                              Ollama (Local LLM)
```

---

## Step 1: Supabase (PostgreSQL) — Free

1. Go to https://supabase.com and sign up (free)
2. Click **"New Project"**
   - Organization: Create new
   - Project name: `nexusbi`
   - Database password: Generate a strong password (save it!)
   - Region: Closest to you
3. Wait for project to be created (~2 min)
4. Go to **Settings → Database** and copy:
   - Host: `db.xxxxx.supabase.co`
   - Port: `5432`
   - Database: `postgres`
   - User: `postgres`
   - Password: (the one you set)
5. Go to **Settings → API** and copy:
   - Project URL: `https://xxxxx.supabase.co`
   - API Key: `eyJhbG...` (anon key)

**Save these values — you'll need them later.**

---

## Step 2: Upstash (Redis) — Free

1. Go to https://upstash.com and sign up (free)
2. Click **"Create Database"**
   - Name: `nexusbi`
   - Type: Regional (closest to you)
   - Plan: **Free**
3. Go to **Connect** tab and copy:
   - Redis URL: `rediss://default:xxxxx@xxxxx.upstash.io:6379`

**Save this URL — you'll need it later.**

---

## Step 3: Railway (Backend) — Free ($5/mo credit)

1. Go to https://railway.app and sign up with GitHub
2. Click **"New Project" → "Deploy from GitHub repo"**
3. Select your `NexusBI` repository
4. Railway will auto-detect Docker — select the **backend** directory
5. Go to **Variables** tab and add:

```env
ENV=production
DEBUG=false
SECRET_KEY=<generate: python3 -c "import secrets; print(secrets.token_hex(32))">

# PostgreSQL (from Supabase)
POSTGRES_HOST=db.xxxxx.supabase.co
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<your_supabase_password>

# Redis (from Upstash)
REDIS_HOST=xxxxx.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=<your_upstash_password>

# LLM (use mock for now, add Ollama later)
LLM_PROVIDER=mock

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_AGENT_REQUESTS_PER_MINUTE=10
```

6. Go to **Settings**:
   - Build: Dockerfile in `backend/`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Healthcheck Path: `/health`
7. Click **Deploy**
8. Wait for deployment (~3-5 min)
9. Copy your Railway domain: `https://nexusbi-xxxxx.up.railway.app`

**Test it:**
```bash
curl https://nexusbi-xxxxx.up.railway.app/health
```

---

## Step 4: Vercel (Frontend) — Free

1. Go to https://vercel.com and sign up with GitHub
2. Click **"New Project" → "Import Git Repository"**
3. Select your `NexusBI` repository
4. Configure:
   - Framework Preset: **Next.js**
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `.next`
5. Go to **Environment Variables** and add:

```env
NEXT_PUBLIC_API_URL=https://nexusbi-xxxxx.up.railway.app/api/v1
```

6. Click **Deploy**
7. Wait for deployment (~2 min)
8. Copy your Vercel domain: `https://nexusbi.vercel.app`

---

## Step 5: Database Migration

Run migrations against your Supabase database:

```bash
# Option A: Run locally against Supabase
cd backend
export POSTGRES_HOST=db.xxxxx.supabase.co
export POSTGRES_PORT=5432
export POSTGRES_DB=postgres
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=<your_supabase_password>

uv run python -m alembic upgrade head
uv run python -m app.infrastructure.database.seed

# Option B: Use Railway shell
# In Railway dashboard → your service → Shell
python -m alembic upgrade head
python -m app.infrastructure.database.seed
```

---

## Step 6: Custom Domain (Optional — Free)

1. **Cloudflare** (https://cloudflare.com):
   - Sign up free
   - Add your domain
   - Update nameservers at your registrar

2. **Vercel** (frontend):
   - Go to your project → Settings → Domains
   - Add `app.yourdomain.com`
   - Vercel auto-configures SSL

3. **Railway** (backend):
   - Go to your service → Settings → Networking
   - Add `api.yourdomain.com`
   - Railway auto-configures SSL

4. **Update frontend** env var:
   ```
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
   ```

---

## Step 7: Local Ollama (Optional — Free LLM)

If you want real NL→SQL without paying for API:

1. Install Ollama on your machine:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. Pull a model:
   ```bash
   ollama pull llama3.1
   ```

3. Expose Ollama to the internet (for Railway to reach it):
   ```bash
   # Using ngrok (free)
   ngrok http 11434
   ```
   This gives you: `https://xxxxx.ngrok.io`

4. Update Railway env:
   ```
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=https://xxxxx.ngrok.io
   OLLAMA_MODEL=llama3.1
   ```

**Note:** ngrok free tier restarts every 8 hours. For production, consider
a $5/month VPS with Ollama running on it.

---

## Step 8: Verify Deployment

```bash
# Health check
curl https://nexusbi-xxxxx.up.railway.app/health

# Login
curl -X POST https://nexusbi-xxxxx.up.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@nexusbi.io","password":"SecureP@ssw0rd!"}'

# Open frontend
open https://nexusbi.vercel.app
```

Login with:
- Email: `admin@nexusbi.io`
- Password: `SecureP@ssw0rd!`

---

## Cost Breakdown

| Service | Plan | Cost |
|---|---|---|
| Supabase | Free | $0/mo |
| Upstash | Free | $0/mo |
| Railway | Free ($5 credit) | $0/mo |
| Vercel | Free | $0/mo |
| Cloudflare | Free | $0/mo |
| **Total** | | **$0/mo** |

### When you outgrow free tiers:

| Service | Paid Plan | Cost |
|---|---|---|
| Railway | Starter | $5/mo |
| Supabase | Pro | $25/mo |
| Upstash | Pay-as-you-go | ~$2/mo |

---

## Environment Variables Reference

```env
# Application
ENV=production
DEBUG=false
SECRET_KEY=<random-64-char-hex>

# PostgreSQL (Supabase)
POSTGRES_HOST=db.xxxxx.supabase.co
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<supabase-password>

# Redis (Upstash)
REDIS_HOST=xxxxx.upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=<upstash-password>

# LLM
LLM_PROVIDER=mock  # or "ollama" with OLLAMA_BASE_URL
OLLAMA_BASE_URL=https://your-ollama-url
OLLAMA_MODEL=llama3.1

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_AGENT_REQUESTS_PER_MINUTE=10

# CORS
ALLOWED_ORIGINS=["https://yourdomain.com"]
ALLOWED_HOSTS=["yourdomain.com"]
```

---

## Troubleshooting

### Backend won't start
- Check Railway logs: Service → Logs
- Ensure all env vars are set
- Verify PostgreSQL connection: `curl /health`

### Frontend can't reach backend
- Check `NEXT_PUBLIC_API_URL` env var
- Ensure it includes `/api/v1` suffix
- Verify CORS: `ALLOWED_ORIGINS` must include your frontend domain

### Database migration fails
- Ensure Supabase project is active
- Check credentials are correct
- Try running migrations manually via Railway shell

### Ollama not responding
- Ensure Ollama is running: `ollama list`
- Check ngrok URL is active
- Verify model is pulled: `ollama pull llama3.1`
