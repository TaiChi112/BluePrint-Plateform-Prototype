# Deployment Guide - Blueprint Hub

**Document Version**: 1.0  
**Last Updated**: March 2, 2026  
**Status**: 🚧 Template (Ready for Q3 2026 Production Deployment)  
**Owner:** DevOps Engineer + Tech Lead

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Environment Configuration](#3-environment-configuration)
4. [Frontend Deployment (Vercel)](#4-frontend-deployment-vercel)
5. [Backend Deployment (Railway)](#5-backend-deployment-railway)
6. [Database Setup (Supabase/Railway)](#6-database-setup-supabaserailway)
7. [Post-Deployment Verification](#7-post-deployment-verification)
8. [Rollback Procedures](#8-rollback-procedures)
9. [Troubleshooting](#9-troubleshooting)
10. [Monitoring & Alerts](#10-monitoring--alerts)

---

## 1. Overview

### 1.1 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRODUCTION ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
│                 │          │                 │          │                 │
│   VERCEL CDN    │◄────────►│   RAILWAY       │◄────────►│   SUPABASE      │
│   (Frontend)    │   HTTPS  │   (Backend)     │   TCP    │   (PostgreSQL)  │
│                 │          │                 │          │                 │
│  Next.js 16     │          │  FastAPI        │          │  PostgreSQL 14+ │
│  React 19       │          │  Python 3.11    │          │  Prisma ORM     │
│  TypeScript     │          │  LLM (OpenAI)   │          │                 │
│                 │          │                 │          │                 │
└─────────────────┘          └─────────────────┘          └─────────────────┘
        │                            │                            │
        │                            │                            │
        └────────────────────────────┴────────────────────────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │   EXTERNAL SERVICES   │
                          │   - OpenAI API        │
                          │   - GitHub OAuth      │
                          │   - Google OAuth      │
                          └─────────────────────┘
```

### 1.2 Deployment Strategy

**Approach:** Blue-Green Deployment with phased rollout

**Rollout Phases:**
1. **Phase 1 (Internal):** Deploy to staging → Internal team testing (1 week)
2. **Phase 2 (Beta):** Production deployment → 10% users (beta testers) (1 week)
3. **Phase 3 (Gradual):** Increase to 50% users (1 week)
4. **Phase 4 (Full):** 100% users (monitor for 72 hours)

**Rollback Time:** <15 minutes (automated rollback to previous version)

---

## 2. Prerequisites

### 2.1 Required Accounts & Access

- [ ] **Vercel Account** (Team plan recommended)
  - Account owner: [DevOps Lead email]
  - Team members: [Frontend Lead, Tech Lead]
  - Payment method configured

- [ ] **Railway Account** (Pro plan for production)
  - Account owner: [DevOps Lead email]
  - Team members: [Backend Lead, Tech Lead]
  - Payment method configured

- [ ] **Supabase Account** (Pro plan recommended)
  - Account owner: [DevOps Lead email]
  - Team members: [Database Admin, Tech Lead]
  - Payment method configured

- [ ] **GitHub Repository Access**
  - Repository: `TaiChi112/BluePrint-Plateform-Prototype`
  - Permissions: Admin (for deployment key setup)

- [ ] **OpenAI API Key**
  - Organization: [Your Organization]
  - API key: Production key (separate from dev/staging)
  - Billing: Production usage tier

### 2.2 Required Secrets & Environment Variables

**Collect Before Deployment:**
```bash
# Frontend (.env.production)
DATABASE_URL=                    # Supabase PostgreSQL connection string
NEXTAUTH_URL=                    # https://blueprint-hub.com
NEXTAUTH_SECRET=                 # Generate: openssl rand -base64 32
GOOGLE_CLIENT_ID=                # OAuth credentials
GOOGLE_CLIENT_SECRET=            # OAuth credentials
GITHUB_ID=                       # OAuth credentials
GITHUB_SECRET=                   # OAuth credentials
NEXT_PUBLIC_API_URL=             # https://api.blueprint-hub.com

# Backend (.env.production)
DATABASE_URL=                    # Same as frontend (Supabase)
OPENAI_API_KEY=                  # Production OpenAI key
CORS_ORIGINS=                    # https://blueprint-hub.com
ENVIRONMENT=production
LOG_LEVEL=info
RATE_LIMIT_PER_MINUTE=10         # API rate limiting
```

**Secret Management:**
- Use **Vercel Environment Variables** (encrypted)
- Use **Railway Environment Variables** (encrypted)
- **DO NOT** commit secrets to Git

---

## 3. Environment Configuration

### 3.1 Development Environment

```bash
# Frontend: localhost:3001
# Backend: localhost:8000
# Database: PostgreSQL (local Docker or Railway dev instance)
```

**Purpose:** Local development and testing

### 3.2 Staging Environment

```bash
# Frontend: https://staging.blueprint-hub.vercel.app
# Backend: https://api-staging.blueprint-hub.railway.app
# Database: Supabase staging instance
```

**Purpose:** Pre-production testing, QA validation

### 3.3 Production Environment

```bash
# Frontend: https://blueprint-hub.com (custom domain)
# Backend: https://api.blueprint-hub.com (custom domain)
# Database: Supabase production instance
```

**Purpose:** Live user traffic

---

## 4. Frontend Deployment (Vercel)

### 4.1 Initial Setup (One-Time)

**Step 1: Import GitHub Repository to Vercel**

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Import Project"**
3. Select **"Import Git Repository"**
4. Choose: `TaiChi112/BluePrint-Plateform-Prototype`
5. **Framework Preset**: Next.js
6. **Root Directory**: `frontend/`

**Step 2: Configure Environment Variables**

1. In Vercel project settings → **"Environment Variables"**
2. Add all variables from Section 2.2 (Frontend)
3. Set **Environment**: Production
4. Click **"Save"**

**Step 3: Configure Custom Domain**

1. Go to **"Domains"** tab
2. Add domain: `blueprint-hub.com`
3. Add domain: `www.blueprint-hub.com` (redirect to primary)
4. Configure DNS records (provided by Vercel):
   ```
   A record:     blueprint-hub.com → 76.76.21.21
   CNAME record: www.blueprint-hub.com → cname.vercel-dns.com
   ```

**Step 4: Configure Build Settings**

```json
{
  "buildCommand": "cd frontend && bun run build",
  "installCommand": "cd frontend && bun install",
  "outputDirectory": "frontend/.next",
  "framework": "nextjs"
}
```

### 4.2 Deployment Process

**Automatic Deployment (Recommended):**

```bash
# Push to main branch triggers automatic deployment
git add frontend/
git commit -m "feat: add new feature"
git push origin main

# Vercel will automatically:
# 1. Detect changes in frontend/
# 2. Run build process
# 3. Deploy to production
# 4. Run health checks
# 5. Swap traffic (blue-green deployment)
```

**Manual Deployment (If Needed):**

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy from frontend folder
cd frontend/
vercel --prod

# Follow prompts:
# - Link to existing project? Yes
# - Which scope? [Your Team]
# - Which project? blueprint-hub
# - Deploy to production? Yes
```

### 4.3 Post-Deployment Verification (Frontend)

```bash
# 1. Check deployment status
curl -I https://blueprint-hub.com
# Expected: HTTP/2 200

# 2. Verify API connectivity
curl https://blueprint-hub.com/api/health
# Expected: {"status": "ok", "version": "1.0"}

# 3. Test authentication
# - Navigate to https://blueprint-hub.com/signin
# - Click "Sign in with Google"
# - Verify OAuth flow completes

# 4. Check error monitoring
# - Open Vercel Dashboard → Analytics
# - Verify no error spikes

# 5. Performance check
# - Vercel Analytics → Speed Insights
# - Expected: First Contentful Paint <1.5s
```

---

## 5. Backend Deployment (Railway)

### 5.1 Initial Setup (One-Time)

**Step 1: Create Railway Project**

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose: `TaiChi112/BluePrint-Plateform-Prototype`
5. **Root Directory**: `backend/`

**Step 2: Configure Environment Variables**

1. In Railway project → **"Variables"** tab
2. Add all variables from Section 2.2 (Backend)
3. Enable **"Redact Secrets"** (hide in logs)

**Step 3: Configure Custom Domain**

1. Go to **"Settings"** tab
2. Click **"Generate Domain"** (temporary: `blueprint-hub-backend.railway.app`)
3. Add custom domain: `api.blueprint-hub.com`
4. Configure DNS:
   ```
   CNAME record: api.blueprint-hub.com → blueprint-hub-backend.railway.app
   ```

**Step 4: Configure Build & Start Commands**

```toml
# railway.toml (in backend/ folder)
[build]
builder = "nixpacks"
buildCommand = "uv pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on-failure"
```

### 5.2 Deployment Process

**Automatic Deployment:**

```bash
# Push to main branch triggers automatic deployment
git add backend/
git commit -m "fix: improve LLM response handling"
git push origin main

# Railway will automatically:
# 1. Detect changes in backend/
# 2. Build Docker image (Nixpacks)
# 3. Run migrations (if configured)
# 4. Deploy new version
# 5. Health check passes → swap traffic
```

**Manual Deployment (If Needed):**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to project
railway link

# Deploy
railway up

# Check deployment status
railway status
```

### 5.3 Post-Deployment Verification (Backend)

```bash
# 1. Check health endpoint
curl https://api.blueprint-hub.com/health
# Expected: {"status": "healthy", "database": "connected"}

# 2. Test spec generation endpoint
curl -X POST https://api.blueprint-hub.com/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Build a todo app"}' \
  -H "Authorization: Bearer [test-token]"
# Expected: 200 OK with generated spec

# 3. Check database connectivity
curl https://api.blueprint-hub.com/db-status
# Expected: {"status": "connected", "latency_ms": "<100"}

# 4. Monitor logs
railway logs
# Expected: No errors, successful requests logged

# 5. Performance check
# - Railway Dashboard → Metrics
# - Expected: CPU <50%, Memory <512MB
```

---

## 6. Database Setup (Supabase/Railway)

### 6.1 Supabase Setup (Recommended)

**Step 1: Create Supabase Project**

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Click **"New Project"**
3. **Project Name**: blueprint-hub-prod
4. **Database Password**: [Generate strong password]
5. **Region**: US West (or closest to users)

**Step 2: Run Prisma Migrations**

```bash
# From frontend/ folder
cd frontend/

# Set production database URL
export DATABASE_URL="postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"

# Run migrations
bunx prisma migrate deploy

# Expected output:
# ✓ 5 migrations applied successfully
```

**Step 3: Seed Production Data (Optional)**

```bash
# Seed initial data (if needed)
bunx prisma db seed

# Verify seed data
bunx prisma studio
```

**Step 4: Configure Connection Pooling**

1. Go to Supabase project → **"Database"** → **"Settings"**
2. Enable **"Connection Pooling"** (Supavisor)
3. Use pooled connection string for backend:
   ```
   postgresql://postgres:[password]@[project-ref].pooler.supabase.com:5432/postgres
   ```

### 6.2  Database Backups

**Automatic Backups (Supabase):**
- **Daily backups**: Enabled by default (retained 7 days)
- **Point-in-time recovery**: Available (Pro plan)

**Manual Backup (Before Major Deployment):**

```bash
# Export database to SQL file
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql

# Upload to secure storage (AWS S3, Google Drive, etc.)
# Store in: backups/production/backup-YYYYMMDD.sql
```

### 6.3 Post-Deployment Verification (Database)

```bash
# 1. Verify tables exist
bunx prisma db pull
# Expected: Schema matches prisma/schema.prisma

# 2. Check data integrity
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
# Expected: Row count matches expected

# 3. Test query performance
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM projects LIMIT 10;"
# Expected: Execution time <50ms

# 4. Monitor active connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
# Expected: <20 active connections (under load)
```

---

## 7. Post-Deployment Verification

### 7.1 Full System Health Check

```bash
# Run automated health check script
./scripts/health-check-prod.sh

# Contents of health-check-prod.sh:
#!/bin/bash
echo "Running production health checks..."

# Frontend health
echo "1. Frontend..."
curl -sf https://blueprint-hub.com/api/health || echo "❌ Frontend unhealthy"

# Backend health
echo "2. Backend..."
curl -sf https://api.blueprint-hub.com/health || echo "❌ Backend unhealthy"

# Database health
echo "3. Database..."
curl -sf https://api.blueprint-hub.com/db-status || echo "❌ Database unhealthy"

# Authentication
echo "4. Authentication..."
curl -sf https://blueprint-hub.com/api/auth/session || echo "❌ Auth unhealthy"

# LLM integration
echo "5. LLM integration..."
# [Test API call to LLM endpoint]

echo "✅ All health checks passed!"
```

### 7.2 Critical User Flows (Smoke Tests)

**Test manually or with E2E automation:**

1. **User Registration & Login**
   - [ ] Google OAuth works
   - [ ] GitHub OAuth works
   - [ ] Session persists after login

2. **Blueprint Creation**
   - [ ] Create new blueprint
   - [ ] AI generation works (<8s response time)
   - [ ] Save blueprint successfully

3. **Multi-Turn Conversation**
   - [ ] Refine blueprint with conversation
   - [ ] Conversation history persists
   - [ ] Updates saved correctly

4. **Version Tracking**
   - [ ] Create new version (V0.1 → V1.0)
   - [ ] Version history displays correctly

5. **Publish & Share**
   - [ ] Publish blueprint (isPublished=true)
   - [ ] Published blueprint visible on homepage
   - [ ] Share link works

### 7.3 Performance Benchmarking

```bash
# Use Apache Bench (ab) or k6 for load testing
ab -n 100 -c 10 https://blueprint-hub.com/
# Expected: 
# - 95% requests <2s
# - 0% failed requests

# Backend API load test
ab -n 100 -c 10 -p test-payload.json -T application/json \
   https://api.blueprint-hub.com/generate
# Expected:
# - 90% requests <8s (AI generation)
# - 0% failed requests
```

---

## 8. Rollback Procedures

### 8.1 Frontend Rollback (Vercel)

**Automatic Rollback (via Vercel Dashboard):**

1. Go to Vercel Dashboard → **"Deployments"**
2. Find previous successful deployment
3. Click **"..."** menu → **"Promote to Production"**
4. Confirm rollback
5. **Time to rollback:** <2 minutes

**Manual Rollback (via Git):**

```bash
# Revert to previous commit
git log --oneline frontend/
# Find previous working commit SHA

git revert [commit-SHA]
git push origin main

# Vercel auto-deploys reverted version
```

### 8.2 Backend Rollback (Railway)

**Via Railway Dashboard:**

1. Go to Railway Dashboard → **"Deployments"**
2. Find previous successful deployment
3. Click **"Redeploy"**
4. **Time to rollback:** <5 minutes

**Via Railway CLI:**

```bash
railway status --json | jq '.deployments[1].id'
# Get previous deployment ID

railway rollback [deployment-id]
```

### 8.3 Database Rollback (Critical)

**⚠️ Use with extreme caution - may cause data loss**

**Option 1: Prisma Migration Rollback**

```bash
# List applied migrations
bunx prisma migrate status

# Rollback last migration
bunx prisma migrate resolve --rolled-back [migration-name]

# Re-apply if needed
bunx prisma migrate deploy
```

**Option 2: Restore from Backup**

```bash
# Download latest backup
# (from Supabase Dashboard or S3)

# Restore database
psql $DATABASE_URL < backup-20260302.sql

# Verify restoration
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
```

---

## 9. Troubleshooting

### 9.1 Common Issues & Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **Frontend build fails** | Vercel deployment error | Check build logs → Verify `bun.lock` is committed → Check environment variables |
| **Backend won't start** | Railway health check fails | Check logs → Verify `DATABASE_URL` correct → Check uvicorn start command |
| **Database connection fails** | "Unable to connect to database" | Verify Supabase connection string → Check IP whitelist → Test with `psql` |
| **OAuth not working** | Google/GitHub login fails | Verify OAuth callback URL → Check client ID/secret → Enable OAuth in provider console |
| **LLM generation slow** | >10s response time | Check OpenAI API status → Increase rate limit → Optimize prompt |
| **High latency** | Slow page loads | Check CDN cache hit rate → Enable compression → Optimize database queries |

### 9.2 Emergency Contact List

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| **DevOps Lead** | [Name] | [Email/Phone] | 24/7 (on-call) |
| **Tech Lead** | [Name] | [Email/Phone] | Mon-Fri 9AM-6PM |
| **Backend Lead** | [Name] | [Email/Phone] | Mon-Fri 9AM-6PM |
| **Database Admin** | [Name] | [Email/Phone] | Mon-Fri 9AM-6PM |
| **Vercel Support** | - | [Vercel Support URL] | 24/7 (Team plan) |
| **Railway Support** | - | [Railway Support URL] | 24/7 (Pro plan) |
| **Supabase Support** | - | [Supabase Support URL] | 24/7 (Pro plan) |

---

## 10. Monitoring & Alerts

### 10.1 Monitoring Setup (Grafana + Prometheus - Optional)

**Coming in Q3 2026:**

- Real-time performance dashboards
- Error rate monitoring
- Database query performance
- API response times
- User activity metrics

**For Now (Q2 2026):**
- Use Vercel Analytics (frontend)
- Use Railway Metrics (backend)
- Use Supabase Monitoring (database)

### 10.2 Alert Configuration

**Set up alerts for:**

- [ ] Error rate >5% (last 5 minutes) → Slack notification
- [ ] Response time P95 >5 seconds → Email to DevOps
- [ ] Database connection pool exhausted → PagerDuty alert
- [ ] Deploy failure → Slack notification
- [ ] Certificate expiration <30 days → Email to DevOps

---

## 11. Post-Production Checklist

**Complete within 72 hours of deployment:**

- [ ] Verify all smoke tests pass (Section 7.2)
- [ ] Monitor error logs for first 24 hours
- [ ] Confirm backup schedule running
- [ ] Update status page (if applicable)
- [ ] Send deployment summary to stakeholders
- [ ] Schedule post-mortem meeting (if issues occurred)
- [ ] Update SDLC.md Section 9 (mark Deployment Guide as ✅ Complete)

---

## 12. References

- [SDLC.md](../SDLC.md) - Section 4.4 (Deployment Architecture)
- [docs/diagrams/deployment.md](diagrams/deployment.md) - Deployment diagrams
- [Vercel Documentation](https://vercel.com/docs)
- [Railway Documentation](https://docs.railway.app/)
- [Supabase Documentation](https://supabase.com/docs)
- [Prisma Deployment Guide](https://www.prisma.io/docs/guides/deployment)

---

**Maintained By:** DevOps Engineer  
**Review Cycle:** Before each major deployment  
**Last Production Deployment:** [TBD - Q3 2026]
