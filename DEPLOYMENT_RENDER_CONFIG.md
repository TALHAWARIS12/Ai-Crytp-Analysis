# Render Deployment Configuration Guide

## Overview
This guide explains how to properly configure the AI Crypto Trading Assistant on Render to avoid URL routing issues and other common problems.

## Critical Issues & Fixes

### Issue 1: Double `/api/v1` in URLs (404 Not Found)
**Problem**: Requests are going to `/api/v1/api/v1/analyze` instead of `/api/v1/analyze`

**Root Cause**: Incorrect `NEXT_PUBLIC_API_URL` environment variable in Render

**Solution**:
1. Go to your frontend service on Render dashboard
2. Navigate to **Settings** → **Environment**
3. Set the following environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-domain.onrender.com
   ```
   **Important**: Do NOT include `/api/v1` in the URL
4. Redeploy the frontend service

### Issue 2: 503 Service Unavailable (Market Data Errors)
**Problem**: `/api/v1/price/{symbol}` returns 503 errors

**Causes**:
- **IP Location Restriction**: Binance blocks certain IP ranges (including some cloud providers)
- **Rate Limiting**: Too many requests to Binance API too quickly
- **API Credentials**: Missing or invalid Binance API keys
- **Network Issues**: Connection timeouts

**Solutions**:

#### Solution A: Use VPN/Proxy (Recommended for Render)
Since Render's IPs may be restricted by Binance:

1. Set up an HTTP proxy service or use a Binance API proxy
2. Configure in backend environment:
   ```
   BINANCE_API_PROXY=https://your-proxy-service.com
   ```

#### Solution B: Add Binance API Credentials
1. Get API keys from Binance:
   - Log in to Binance
   - Security → API Management
   - Create new API key with "Spot" and "Margin" permissions (disable withdrawal)
2. In Render backend settings, add:
   ```
   BINANCE_API_KEY=your_api_key_here
   BINANCE_API_SECRET=your_api_secret_here
   ```
   
#### Solution C: Implement Request Caching
To reduce API calls, add Redis caching (see updated backend code)

### Issue 3: CORS Errors When Frontend Talks to Backend
**Problem**: Frontend gets CORS errors when calling API

**Solution**: 
Backend already has CORS middleware, but verify in `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],  # Must match frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Ensure in backend environment:
```
FRONTEND_URL=https://your-frontend-domain.onrender.com
```

## Render Environment Variables Checklist

### Frontend Service
```
NEXT_PUBLIC_API_URL=https://your-backend-domain.onrender.com
NODE_ENV=production
```

### Backend Service
```
FRONTEND_URL=https://your-frontend-domain.onrender.com
DATABASE_URL=postgresql://user:password@host:5432/dbname
TELEGRAM_BOT_TOKEN=your_bot_token_or_skip
BINANCE_API_KEY=your_key_or_leave_empty
BINANCE_API_SECRET=your_secret_or_leave_empty
```

## Deployment Checklist

- [ ] Frontend `NEXT_PUBLIC_API_URL` set correctly (NO `/api/v1` in URL)
- [ ] Backend `FRONTEND_URL` matches your frontend domain
- [ ] Backend service is deployed before frontend
- [ ] CORS middleware in backend is configured
- [ ] Database migrations run successfully (if using database)
- [ ] Check Render logs for errors after deployment
- [ ] Test API endpoints from browser console:
  ```javascript
  fetch('https://your-backend.onrender.com/api/v1/price/BTCUSDT')
    .then(r => r.json())
    .then(d => console.log(d))
  ```

## Debugging Steps

1. **Check frontend logs**:
   - Open browser DevTools → Network tab
   - Look for actual URLs being requested
   - Should be: `https://your-backend.onrender.com/api/v1/...`
   - NOT: `https://your-backend.onrender.com/api/v1/api/v1/...`

2. **Check backend logs**:
   - Render dashboard → Backend service → Logs
   - Look for error messages with exception types
   - Example: `[NetworkError] Connect timeout reached`

3. **Test endpoints directly**:
   ```bash
   # Test health check
   curl https://your-backend.onrender.com/health
   
   # Test price endpoint
   curl https://your-backend.onrender.com/api/v1/price/BTCUSDT
   
   # Test analyze endpoint
   curl -X POST https://your-backend.onrender.com/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d '{"symbol":"BTC/USDT"}'
   ```

## Fixing After Deployment

If you see errors after deployment:

1. **Fix environment variables** in Render dashboard
2. **Rebuild/redeploy** the affected service
3. **Clear browser cache** (Ctrl+Shift+Delete)
4. **Wait 30 seconds** for deployment to complete
5. **Check logs** to verify the fix worked

## Production Recommendations

1. **Enable Caching**: Add Redis to cache market prices (1-5 minute TTL)
2. **Rate Limiting**: Implement API rate limiting on backend
3. **Monitoring**: Set up error alerting for 503 responses
4. **Fallback Data**: Cache last known prices for resilience
5. **API Rotation**: Rotate between multiple market data sources

## References

- [Render Documentation](https://render.com/docs)
- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
- [Next.js Environment Variables](https://nextjs.org/docs/basic-features/environment-variables)
- [CCXT Binance Documentation](https://docs.ccxt.com/en/latest/manual/exchanges/binance.html)
