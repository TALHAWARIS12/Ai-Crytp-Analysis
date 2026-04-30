# AI Crypto Trading Assistant

A **production-grade**, institutional-quality crypto trading analysis system featuring real market data integration, AI-powered analysis, and professional-grade technical indicators.

## 🎯 Core Features

### ✅ Real Market Data Integration
- **Live Binance Futures API** via CCXT wrapper
- Multi-timeframe analysis (15m, 1h, 4h, 1d)
- Order book, funding rates, open interest
- Automatic retry logic and error handling
- Sub-second API response times

### ✅ Technical Analysis Engine
- **10+ Professional Indicators**
  - EMA 8/34 crossovers
  - SMA 50/200 alignment
  - RSI, MACD, ATR, VWAP
  - Bollinger Bands
  - Volume analysis
  - Support/resistance detection
  - Higher highs/lows identification

### ✅ Strategy Validation
- Real-time strategy testing against live data
- Risk/reward ratio analysis
- Entry/exit zone calculation
- Volume confirmation
- Overextension detection
- Late entry warnings

### ✅ Signal Verification
- User signal validation against market conditions
- Risk assessment scoring (0-100%)
- Funding rate impact analysis
- Volume strength evaluation
- Resistance/support relationship check
- Professional recommendations (VALID/WAIT/AVOID/RISKY)

### ✅ AI Reasoning Layer
- GPT-4 powered trader perspective
- Structured data → AI (prevents hallucinations)
- Professional analysis formatting
- Fallback analysis if API unavailable
- Trained reasoning patterns

### ✅ Telegram Bot
- `/analyze BTCUSDT` - Full analysis
- `/strategy ETHUSDT LONG 4H` - Validate setup
- `/checksignal` - Verify signal
- `/help` - Command reference
- Natural language support
- Formatted professional output

### ✅ Premium Web Dashboard
- Dark theme (Bloomberg-like aesthetic)
- Responsive design (mobile → ultrawide)
- Live price updates
- Multi-timeframe charts
- Search any symbol
- Watchlist management
- Professional UI components
- Smooth transitions and animations

### ✅ Production-Ready Architecture
- Docker containerization
- Nginx reverse proxy with rate limiting
- PostgreSQL persistence
- Redis caching
- Async Python backend (FastAPI)
- TypeScript React frontend
- Comprehensive error handling
- Health checks on all services

---

## 🏗️ System Architecture

```
┌────────────────────────────────────────────┐
│         Telegram Bot / Web Dashboard        │
│    (aiogram / Next.js TypeScript)           │
└────────────────────┬───────────────────────┘
                     │
    ┌────────────────┴────────────────┐
    │                                 │
┌───▼──────────────┐      ┌──────────▼──┐
│  FastAPI Backend │      │    Nginx    │
│  (Python 3.12)  │◄─────┤   Reverse   │
│  - Analytics    │      │   Proxy     │
│  - Strategies   │      └─────────────┘
│  - AI Reasoning │
└────┬────────────┘
     │
  ┌──┴──────────────┬──────────────┐
  │                 │              │
┌─▼────┐      ┌─────▼──┐    ┌─────▼─────┐
│  DB  │      │ Cache  │    │  Binance  │
│ PSQL │      │ Redis  │    │ Futures   │
└──────┘      └────────┘    │   API     │
                            └───────────┘
```

---

## 📦 Tech Stack

### Backend
- **Framework**: FastAPI (async)
- **Data**: CCXT, pandas, numpy
- **Analysis**: ta-lib, custom indicators
- **AI**: OpenAI GPT-4 API
- **Database**: PostgreSQL
- **Cache**: Redis
- **Bot**: aiogram (Telegram)
- **Language**: Python 3.12

### Frontend
- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State**: Zustand
- **UI**: Recharts, custom components
- **API Client**: Axios with SWR

### Deployment
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Reverse Proxy**: Nginx
- **Ready for**: Kubernetes, AWS, DigitalOcean

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone and setup
git clone <repo>
cd ai-crypto-trading-assistant

# Copy environment template
cp docker/.env.example docker/.env

# Edit with your API keys
nano docker/.env

# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run_server.py  # http://localhost:8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev  # http://localhost:3000
```

---

## 📊 API Examples

### Analyze a Coin
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT"}'
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "current_price": 108250.50,
  "trend": "BULLISH",
  "confidence": 78.5,
  "support": [107400, 106900],
  "resistance": [108800, 109500],
  "ema8": 108100,
  "ema34": 107500,
  "rsi": 62.3,
  "analysis": "Strong bullish momentum with price above MA200...",
  "timestamp": "2026-04-28T..."
}
```

### Validate Strategy
```bash
curl -X POST http://localhost:8000/api/v1/strategy \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "ETHUSDT",
    "direction": "LONG",
    "timeframe": "4h"
  }'
```

### Check Signal
```bash
curl -X POST http://localhost:8000/api/v1/checksignal \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RAREUSDT",
    "direction": "LONG",
    "entry_price": 0.0179,
    "entry_zone_low": 0.0179,
    "entry_zone_high": 0.0180,
    "targets": [0.0250, 0.0300],
    "stop_loss": 0.0161
  }'
```

---

## 📁 Project Structure

```
ai-crypto-trading-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── api/                 # API routes
│   │   ├── core/                # Configuration
│   │   ├── market_data/         # CCXT integration
│   │   ├── indicators/          # Technical indicators
│   │   ├── strategies/          # Strategy logic
│   │   ├── ai/                  # AI reasoning
│   │   ├── telegram/            # Bot implementation
│   │   ├── db/                  # Database models
│   │   └── schemas/             # Pydantic models
│   ├── tests/                   # Test suite
│   ├── requirements.txt
│   └── run_server.py
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Dashboard
│   │   ├── layout.tsx           # Root layout
│   │   ├── components/          # React components
│   │   └── globals.css          # Global styles
│   ├── lib/
│   │   ├── api.ts               # API client
│   │   └── store.ts             # State management
│   ├── types/
│   │   └── market.ts            # TypeScript types
│   ├── package.json
│   └── tsconfig.json
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── docker-compose.yml
│   └── .env.example
│
├── nginx/
│   └── nginx.conf               # Reverse proxy config
│
├── DEPLOYMENT.md                # Deployment guide
└── README.md                    # This file
```

---

## 🧪 Testing

```bash
# Run all tests
pytest backend/tests/ -v

# Run specific test file
pytest backend/tests/test_indicators.py -v

# Run with coverage
pytest backend/tests/ --cov=app
```

---

## 📈 Supported Indicators & Analysis

### Indicators
✅ EMA 8, 34  
✅ SMA 50, 200  
✅ RSI (14)  
✅ MACD (12, 26, 9)  
✅ ATR (14)  
✅ Bollinger Bands (20, 2)  
✅ VWAP  
✅ OBV  

### Analysis Features
✅ Higher Highs / Lower Lows  
✅ Trend Scoring  
✅ Support/Resistance Detection  
✅ Volume Analysis  
✅ Funding Rate Monitoring  
✅ Open Interest  
✅ Order Book Depth  

---

## 🔐 Security Features

✅ Environment variables for secrets  
✅ JWT authentication ready  
✅ Password hashing (bcrypt)  
✅ Rate limiting (API & General)  
✅ CORS protection  
✅ Input validation  
✅ SQL injection prevention  
✅ Health checks on all services  

---

## 🎯 Key Strengths

1. **Real Data Only** - No fake data, no mocking in production mode
2. **Professional Grade** - Institutional-quality analysis
3. **Fully Functional** - Every button works, every API responds
4. **Production Ready** - Docker, monitoring, error handling
5. **Scalable** - Async architecture, caching, efficient queries
6. **Well Documented** - Code comments, deployment guide, API docs
7. **Tested** - Comprehensive test suite for core modules
8. **Beautiful UI** - Premium dark theme, responsive design
9. **AI Powered** - GPT-4 integration for trader perspective
10. **Complete** - Bot + Dashboard + Backend + DB all included

---

## 🚀 Deployment

### Development
```bash
docker-compose up -d
# All services running on local network
```

### Production
See `DEPLOYMENT.md` for:
- SSL/HTTPS setup
- Domain configuration
- Database backups
- Monitoring setup
- Scaling recommendations
- AWS/DigitalOcean deployment

---

## 📞 Support

### API Documentation
- Interactive docs: `/docs` (Swagger UI)
- ReDoc: `/redoc`

### Logs
```bash
# Backend logs
docker-compose logs backend -f

# Frontend logs
docker-compose logs frontend -f

# All services
docker-compose logs -f
```

---

## ⚠️ Important Notes

1. **NOT an Auto-Trading Bot**: Analysis only, no order execution
2. **Live Data Required**: Requires internet for real market data
3. **API Keys Needed**: OpenAI API key for AI features
4. **Database Required**: PostgreSQL for persistence
5. **Telegram Bot**: Optional, not required for core functionality

---

## 📄 License

Proprietary - AI Crypto Trading Assistant  
All rights reserved.

---

## 🎓 Learning Resource

This codebase demonstrates:
- ✅ Professional FastAPI architecture
- ✅ Real-world async Python patterns
- ✅ Technical indicator calculations
- ✅ API integration (CCXT, OpenAI)
- ✅ Modern React/Next.js practices
- ✅ Docker containerization
- ✅ Database design and ORMs
- ✅ Production-ready error handling
- ✅ Testing best practices
- ✅ AI/ML integration

Perfect for learning professional backend and frontend development!

---

**Built with ❤️ for institutional-grade crypto analysis**
#   A i - C r y p t o  
 