from typing import Dict, List, Optional
from enum import Enum
import math
from app.indicators.technical import TechnicalIndicators
from app.market_data.service import market_data_service
import logging

logger = logging.getLogger(__name__)

class StrategyStatus(Enum):
    VALID_LONG = "VALID LONG"
    VALID_SHORT = "VALID SHORT"
    WAIT_FOR_RETEST = "WAIT FOR RETEST"
    AVOID_ENTRY = "AVOID ENTRY"
    INVALID = "INVALID"

class StrategyValidator:
    """Production strategy validation engine"""

    @staticmethod
    def _is_valid_number(value: Optional[float]) -> bool:
        return isinstance(value, (int, float)) and not math.isnan(value)
    
    @staticmethod
    async def validate_ema_crossover(symbol: str, candles: List[Dict], direction: str = "LONG", timeframe: str = "4h") -> Dict:
        """Validate EMA 8/34 crossover strategy
        
        Args:
            symbol: Trading pair symbol
            candles: OHLCV candles
            direction: LONG or SHORT
            timeframe: Trading timeframe
            
        Returns:
            Validation result with status and reasoning
        """
        if len(candles) < 50:
            return {
                'status': StrategyStatus.INVALID.value,
                'message': 'Insufficient data for analysis',
                'reason': 'Need at least 50 candles'
            }
        
        close_prices = [c['close'] for c in candles]
        high_prices = [c['high'] for c in candles]
        low_prices = [c['low'] for c in candles]
        volumes = [c['volume'] for c in candles]
        
        # Calculate indicators
        ema8 = TechnicalIndicators.ema(close_prices, 8)
        ema34 = TechnicalIndicators.ema(close_prices, 34)
        sma50 = TechnicalIndicators.sma(close_prices, 50)
        sma200 = TechnicalIndicators.sma(close_prices, 200)
        
        current_price = close_prices[-1]
        ema8_val = ema8[-1]
        ema34_val = ema34[-1]
        sma50_val = sma50[-1]
        sma200_val = sma200[-1]
        
        # Trend analysis
        trend_score = TechnicalIndicators.trend_score(ema8, ema34, sma50, sma200, close_prices)
        
        # Volume analysis
        avg_volume = sum(volumes[-20:]) / 20
        current_volume = volumes[-1]
        volume_strength = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Support/Resistance
        sr = TechnicalIndicators.support_resistance(high_prices, low_prices)
        
        reasons = []
        score = 0
        max_score = 10
        has_sma200 = StrategyValidator._is_valid_number(sma200_val)
        if not has_sma200:
            # Do not penalize confidence when MA200 cannot be computed yet.
            max_score -= 1.5
        
        # EMA Alignment (4 points max)
        if direction == "LONG":
            if ema8_val > ema34_val:
                score += 2
                reasons.append("EMA 8 above EMA 34 (bullish alignment)")
            else:
                reasons.append("EMA 8 below EMA 34 (no bullish alignment)")
            
            # Price vs MA200 (3 points)
            if has_sma200 and current_price > sma200_val:
                score += 1.5
                reasons.append(f"Price above MA200 ({current_price:.2f} > {sma200_val:.2f})")
            elif has_sma200:
                reasons.append(f"Price below MA200 ({current_price:.2f} < {sma200_val:.2f})")
            else:
                reasons.append("! MA200 unavailable (need more candles)")
            
            # Price vs MA50 (2 points)
            if current_price > sma50_val:
                score += 1
                reasons.append("Price above MA50 (retest support)")
            else:
                reasons.append("Price below MA50")
            
            # MTF Alignment (2 points)
            mtf_data = await market_data_service.get_multi_timeframe_data(symbol, ['15m', '1h'])
            alignment_score = 0
            for tf, candles_tf in mtf_data.items():
                if candles_tf:
                    closes_tf = [c['close'] for c in candles_tf]
                    e8 = TechnicalIndicators.ema(closes_tf, 8)
                    e34 = TechnicalIndicators.ema(closes_tf, 34)
                    if direction == "LONG" and e8[-1] > e34[-1]: alignment_score += 1
                    if direction == "SHORT" and e8[-1] < e34[-1]: alignment_score += 1
            
            if alignment_score >= 1:
                score += 1.5
                reasons.append(f"MTF alignment: {alignment_score}/2 lower TFs match")
            else:
                reasons.append("MTF divergence: Lower TFs not aligned")

            # Structure (BOS) (1 point)
            structure = TechnicalIndicators.detect_structure(high_prices, low_prices, close_prices)
            if structure['bos']:
                score += 1
                reasons.append(f"Market Structure: BOS {structure['bos_direction']} detected")

            # Volume confirmation (1 point)
            if volume_strength > 0.9:
                score += 1
                reasons.append(f"Volume strength: {volume_strength:.2f}x (confirmed)")
            else:
                reasons.append(f"Volume weak: {volume_strength:.2f}x")
            
            # Entry timing (2 points)
            price_from_high = ((max(high_prices[-20:]) - current_price) / max(high_prices[-20:])) * 100
            if price_from_high > 1:  # Pulled back from high
                score += 1
                reasons.append(f"Pullback from high ({price_from_high:.1f}%)")
            else:
                reasons.append(f"Chasing extended move ({price_from_high:.1f}%)")
            
            # Overextension check
            if current_price < sr['primary_resistance']:
                score += 0.5
            else:
                reasons.append("⚠ Price near/at resistance")
        
        else:  # SHORT
            if ema8_val < ema34_val:
                score += 2
                reasons.append("EMA 8 below EMA 34 (bearish alignment)")
            else:
                reasons.append("EMA 8 above EMA 34")
            
            if has_sma200 and current_price < sma200_val:
                score += 1.5
                reasons.append("Price below MA200")
            elif has_sma200:
                reasons.append("Price above MA200")
            else:
                reasons.append("! MA200 unavailable (need more candles)")
            
            if current_price < sma50_val:
                score += 1
                reasons.append("Price below MA50")
            else:
                reasons.append("Price above MA50")
            
            if volume_strength > 0.9:
                score += 1
                reasons.append(f"Volume strength: {volume_strength:.2f}x")
            else:
                reasons.append(f"Volume weak: {volume_strength:.2f}x")
        
        # Determine status
        confidence = (score / max_score) * 100
        
        if confidence >= 70:
            status = StrategyStatus.VALID_LONG if direction == "LONG" else StrategyStatus.VALID_SHORT
        elif confidence >= 50:
            status = StrategyStatus.WAIT_FOR_RETEST
        else:
            status = StrategyStatus.AVOID_ENTRY
        
        return {
            'status': status.value,
            'confidence': round(confidence, 1),
            'score': round(score, 1),
            'max_score': max_score,
            'reasons': reasons,
            'current_price': current_price,
            'ema8': ema8_val,
            'ema34': ema34_val,
            'sma50': sma50_val,
            'sma200': sma200_val,
            'support_resistance': sr,
            'volume_strength': volume_strength,
            'trend': trend_score['direction'],
            'timeframe': timeframe
        }
    
    @staticmethod
    def validate_setup_zones(candles: List[Dict], direction: str = "LONG") -> Dict:
        """Validate entry/exit zones"""
        if len(candles) < 20:
            return {}
        
        close_prices = [c['close'] for c in candles]
        high_prices = [c['high'] for c in candles]
        low_prices = [c['low'] for c in candles]
        
        current_price = close_prices[-1]
        sr = TechnicalIndicators.support_resistance(high_prices, low_prices)
        
        ema8 = TechnicalIndicators.ema(close_prices, 8)
        sma50 = TechnicalIndicators.sma(close_prices, 50)
        
        if direction == "LONG":
            # Best entry is at primary support or EMA retest
            entry_zones = {
                'primary_zone': {
                    'low': sr['primary_support'],
                    'high': sr['primary_support'] * 1.01
                },
                'secondary_zone': {
                    'low': sma50[-1] * 0.98,
                    'high': sma50[-1]
                }
            }
            
            exit_zones = {
                'take_profit': sr['primary_resistance'],
                'stop_loss': sr['primary_support'] * 0.99
            }
        
        else:  # SHORT
            entry_zones = {
                'primary_zone': {
                    'low': sr['primary_resistance'] * 0.99,
                    'high': sr['primary_resistance']
                },
                'secondary_zone': {
                    'low': sma50[-1],
                    'high': sma50[-1] * 1.02
                }
            }
            
            exit_zones = {
                'take_profit': sr['primary_support'],
                'stop_loss': sr['primary_resistance'] * 1.01
            }
        
        return {
            'entry_zones': entry_zones,
            'exit_zones': exit_zones,
            'current_price': current_price
        }
