from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
from typing import Dict
import asyncio

from app.core.config import settings
from app.db.database import init_db, get_db
from app.schemas.models import (
    AnalyzeRequest, StrategyRequest, SignalCheckRequest,
    CoinAnalysisResponse, StrategyValidationResponse, SignalVerificationResponse,
    HealthResponse
)
from app.market_data.service import market_data_service
from app.indicators.technical import TechnicalIndicators
from app.strategies.validator import StrategyValidator
from app.strategies.signal_verifier import SignalVerifier
from app.ai.reasoning import AIReasoningEngine
from app.telegram.bot import run_bot
from app.services.scheduler import setup_scheduler, shutdown_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Crypto Trading Assistant",
    description="Professional-grade crypto analysis and signal verification",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup/Shutdown
@app.on_event("startup")
async def startup():
    logger.info("Starting AI Crypto Trading Assistant")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}. Continuing without database.")
    
    # Start Telegram bot in the background
    if settings.telegram_bot_token and "your-" not in settings.telegram_bot_token:
        asyncio.create_task(run_bot())
        logger.info("Telegram bot task scheduled")
    else:
        logger.warning("Telegram bot token missing. Bot disabled.")
        
    # Start background scheduler
    setup_scheduler()
    
    logger.info("Backend ready for requests")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down")
    shutdown_scheduler()

# Health Check
@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )

# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/v1/analyze")
async def analyze_coin(request: AnalyzeRequest) -> Dict:
    """Comprehensive coin analysis with technical indicators and AI reasoning"""
    
    try:
        # Validate symbol
        valid = await market_data_service.validate_symbol(request.symbol)
        if not valid:
            # Try to find similar symbols
            suggestions = await market_data_service.search_symbols(request.symbol)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Symbol not found. Did you mean: {suggestions}"
            )
        
        # Fetch market snapshot
        market_data = await market_data_service.get_full_market_snapshot(request.symbol)
        
        if not market_data['candles']:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch market data. Try again in a moment."
            )
        
        # Analyze primary timeframe (4h)
        candles_4h = market_data['candles'].get('4h', [])
        if len(candles_4h) < 50:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Insufficient data for analysis"
            )
        
        # Extract OHLCV
        close_prices = [c['close'] for c in candles_4h]
        high_prices = [c['high'] for c in candles_4h]
        low_prices = [c['low'] for c in candles_4h]
        
        # Calculate indicators
        ema8 = TechnicalIndicators.ema(close_prices, 8)
        ema34 = TechnicalIndicators.ema(close_prices, 34)
        sma50 = TechnicalIndicators.sma(close_prices, 50)
        sma200 = TechnicalIndicators.sma(close_prices, 200)
        rsi = TechnicalIndicators.rsi(close_prices, 14)
        sr = TechnicalIndicators.support_resistance(high_prices, low_prices)
        trend_score = TechnicalIndicators.trend_score(ema8, ema34, sma50, sma200, close_prices)
        
        current_price = close_prices[-1]
        
        # Build analysis data
        analysis_data = {
            'symbol': request.symbol,
            'current_price': current_price,
            'trend': trend_score['direction'],
            'price_above_ma200': bool(sma200[-1] is not None and current_price > sma200[-1]),
            'ema_alignment': trend_score['ema_alignment'],
            'support': sr['support'],
            'resistance': sr['resistance'],
            'volume_strength': 1.0,
            'funding_rate': market_data['funding_rate']['status'] if market_data['funding_rate'] else 'unknown',
            'rsi': rsi[-1] if rsi else None,
            'type': 'full_analysis'
        }
        
        # Get AI reasoning
        ai_analysis = await AIReasoningEngine.analyze_coin(analysis_data)
        
        return {
            'symbol': request.symbol,
            'current_price': current_price,
            'trend': trend_score['direction'],
            'confidence': trend_score['bullish_score'] * 100,
            'support': sr['support'],
            'resistance': sr['resistance'],
            'ema8': ema8[-1],
            'ema34': ema34[-1],
            'sma50': sma50[-1],
            'sma200': sma200[-1],
            'rsi': rsi[-1] if rsi else None,
            'funding_rate': market_data['funding_rate'],
            'open_interest': market_data['open_interest'],
            'analysis': ai_analysis,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@app.post("/api/v1/strategy")
async def validate_strategy(request: StrategyRequest) -> Dict:
    """Validate trading strategy setup"""
    
    try:
        # Fetch candles
        candles = await market_data_service.get_ohlcv(request.symbol, request.timeframe, 100)
        
        if not candles or len(candles) < 50:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Insufficient data"
            )
        
        # Validate strategy
        result = await StrategyValidator.validate_ema_crossover(
            candles,
            direction=request.direction,
            timeframe=request.timeframe
        )
        
        # Get setup zones
        zones = StrategyValidator.validate_setup_zones(candles, request.direction)
        
        # Get AI reasoning
        ai_reasoning = await AIReasoningEngine.validate_strategy_reasoning(result)
        
        return {
            **result,
            'entry_zones': zones.get('entry_zones'),
            'exit_zones': zones.get('exit_zones'),
            'ai_reasoning': ai_reasoning,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Strategy validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )

@app.post("/api/v1/checksignal")
async def check_signal(request: SignalCheckRequest) -> Dict:
    """Verify trading signal against real market data"""
    
    try:
        # Get ticker for current price
        ticker = await market_data_service.get_ticker(request.symbol)
        if not ticker:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cannot fetch current price"
            )
        
        # Verify signal
        result = await SignalVerifier.verify_signal(
            symbol=request.symbol,
            direction=request.direction,
            entry_price=request.entry_price,
            entry_zone_low=request.entry_zone_low,
            entry_zone_high=request.entry_zone_high,
            targets=request.targets,
            stop_loss=request.stop_loss,
            current_price=ticker['last'],
            timeframe=request.timeframe
        )
        
        # Get AI reasoning
        ai_reasoning = await AIReasoningEngine.evaluate_signal(result)
        
        return {
            **result,
            'ai_reasoning': ai_reasoning,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signal check error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signal check failed: {str(e)}"
        )

# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.get("/api/v1/search")
async def search_symbols(q: str) -> Dict:
    """Search for trading symbols"""
    
    if len(q) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query too short"
        )
    
    symbols = await market_data_service.search_symbols(q)
    return {'symbols': symbols}

@app.get("/api/v1/price/{symbol}")
async def get_price(symbol: str) -> Dict:
    """Get current price for symbol"""
    
    try:
        normalized_symbol = market_data_service._normalize_symbol(symbol)
        ticker = await market_data_service.get_ticker(normalized_symbol)
        if ticker:
            return ticker
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Live market price unavailable from exchange"
        )
    except HTTPException:
        raise
    except Exception as e:
        exc_type = type(e).__name__
        exc_msg = str(e) if str(e) else repr(e)
        logger.error(f"Error fetching ticker for {symbol}: [{exc_type}] {exc_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Live market price unavailable from exchange"
        )

# Error handler
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
