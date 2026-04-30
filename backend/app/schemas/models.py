from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AnalyzeRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair (e.g., BTCUSDT)")
    timeframes: Optional[List[str]] = Field(default=["15m", "1h", "4h"], description="Timeframes to analyze")

class StrategyRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair")
    direction: str = Field(..., description="LONG or SHORT")
    timeframe: str = Field(default="4h", description="Strategy timeframe")

class SignalCheckRequest(BaseModel):
    symbol: str = Field(..., description="Trading pair")
    direction: str = Field(..., description="LONG or SHORT")
    entry_price: float = Field(..., description="Entry price level")
    entry_zone_low: float = Field(..., description="Entry zone lower bound")
    entry_zone_high: float = Field(..., description="Entry zone upper bound")
    targets: List[float] = Field(..., description="Target price levels")
    stop_loss: float = Field(..., description="Stop loss price")
    timeframe: Optional[str] = Field(default="4h")

class CoinAnalysisResponse(BaseModel):
    symbol: str
    current_price: float
    trend: str
    confidence: float
    support: List[float]
    resistance: List[float]
    analysis: str
    timestamp: datetime

class StrategyValidationResponse(BaseModel):
    status: str
    confidence: float
    reasons: List[str]
    warnings: Optional[List[str]]
    entry_zones: Dict[str, Any]
    exit_zones: Dict[str, Any]
    ai_reasoning: str
    timestamp: datetime

class SignalVerificationResponse(BaseModel):
    status: str
    confidence: float
    risk_score: float
    reasons: List[str]
    warnings: List[str]
    symbol: str
    direction: str
    entry_price: float
    stop_loss: float
    targets: List[float]
    ai_reasoning: str
    timestamp: datetime

class WatchlistItem(BaseModel):
    symbol: str
    added_at: datetime

class UserWatchlist(BaseModel):
    items: List[WatchlistItem]
    count: int

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
