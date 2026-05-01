# URGENT: Render Environment Setup

## Frontend Service

**Go to Render Dashboard → Frontend Service → Settings → Environment**

Add/Update this variable:
```
NEXT_PUBLIC_API_URL=https://ai-crytp-analysis.onrender.com
```

**IMPORTANT**: 
- Do NOT include `/api/v1` at the end
- Exact value: `https://ai-crytp-analysis.onrender.com`

Then click **Deploy** or **Redeploy** the frontend service.

---

## Backend Service

**Go to Render Dashboard → Backend Service → Settings → Environment**

Ensure these are set:
```
FRONTEND_URL=https://ai-crytp-analysis-1-site.onrender.com
```

---

## Why You're Getting `/api/v1/api/v1/...` 404 Errors

1. Frontend axios is still receiving a wrong base URL from environment
2. The `.env.production` file is used only during build, not at runtime on Render
3. Render environment variables **override** .env files at runtime

**Solution**: Set the correct environment variable in Render dashboard, then redeploy.

---

## After You Set the Environment Variable

Expected results:
- ✅ `GET /api/v1/price/BTCUSDT` → 200 OK (CoinGecko price with caching)
- ✅ `POST /api/v1/analyze` → 200 OK (analysis result)
- ✅ No more `/api/v1/api/v1/...` 404 errors
- ✅ CoinGecko rate limiting handled gracefully
