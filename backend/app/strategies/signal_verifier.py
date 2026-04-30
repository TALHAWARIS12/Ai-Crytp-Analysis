from typing import Dict, List, Optional, Tuple
from enum import Enum
from app.market_data.service import market_data_service
from app.indicators.technical import TechnicalIndicators
import logging

logger = logging.getLogger(__name__)

class SignalValidity(Enum):
    VALID = "VALID"
    WAIT = "WAIT"
    AVOID = "AVOID"
    RISKY = "RISKY"

class SignalVerifier:
    """Production signal verification engine"""
    
    @staticmethod
    async def verify_signal(
        symbol: str,
        direction: str,
        entry_price: float,
        entry_zone_low: float,
        entry_zone_high: float,
        targets: List[float],
        stop_loss: float,
        current_price: float,
        timeframe: str = "4h"
    ) -> Dict:
        """Verify a trading signal against real market data
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            direction: LONG or SHORT
            entry_price: Entry price level
            entry_zone_low: Entry zone lower bound
            entry_zone_high: Entry zone upper bound
            targets: List of target prices
            stop_loss: Stop loss price
            current_price: Current market price
            timeframe: Analysis timeframe
            
        Returns:
            Signal verification result
        """
        
        # Fetch real market data
        candles = await market_data_service.get_ohlcv(symbol, timeframe, 100)
        ticker = await market_data_service.get_ticker(symbol)
        funding = await market_data_service.get_funding_rate(symbol)
        
        if not candles or not ticker:
            return {
                'status': SignalValidity.AVOID.value,
                'reason': 'Unable to fetch market data',
                'confidence': 0
            }
        
        close_prices = [c['close'] for c in candles]
        high_prices = [c['high'] for c in candles]
        low_prices = [c['low'] for c in candles]
        volumes = [c['volume'] for c in candles]
        
        # Calculate indicators
        ema8 = TechnicalIndicators.ema(close_prices, 8)
        ema34 = TechnicalIndicators.ema(close_prices, 34)
        sma200 = TechnicalIndicators.sma(close_prices, 200)
        rsi = TechnicalIndicators.rsi(close_prices, 14)
        atr = TechnicalIndicators.atr(high_prices, low_prices, close_prices, 14)
        
        reasons = []
        warnings = []
        risk_score = 0
        max_risk = 100
        
        # 2. Multi-Timeframe Alignment (MTF)
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
            reasons.append(f"MTF CONFLUENCE: {alignment_score}/2 lower TFs aligned")
        else:
            warnings.append("MTF DIVERGENCE: Short-term trend not matching")
            risk_score += 10

        # 3. Market Structure (BOS)
        structure = TechnicalIndicators.detect_structure(high_prices, low_prices, close_prices)
        if structure['bos']:
            reasons.append(f"BOS DETECTED: Break of structure in {structure['bos_direction']} direction")
            if (direction == "LONG" and structure['bos_direction'] == "UP") or \
               (direction == "SHORT" and structure['bos_direction'] == "DOWN"):
                reasons.append("Structure confirms signal direction")
            else:
                warnings.append("Counter-structure breakout detected")
                risk_score += 10

        # 4. Check Risk/Reward ratio
        if direction == "LONG":
            entry_for_rr = (entry_zone_low + entry_zone_high) / 2
            distance_to_sl = abs(entry_for_rr - stop_loss)
            distances_to_targets = [abs(t - entry_for_rr) for t in targets]
            
            if distance_to_sl > 0:
                rr_ratios = [d / distance_to_sl for d in distances_to_targets]
                avg_rr = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0
                
                if avg_rr >= 2:
                    reasons.append(f"GOOD RR ratio: {avg_rr:.1f}:1 (avg)")
                elif avg_rr >= 1.5:
                    reasons.append(f"ACCEPTABLE RR ratio: {avg_rr:.1f}:1")
                else:
                    warnings.append(f"POOR RR ratio: {avg_rr:.1f}:1 (need >= 2:1)")
                    risk_score += 20
                
                # Check stop loss distance
                sl_distance_pct = (distance_to_sl / entry_for_rr) * 100
                if sl_distance_pct > 5:
                    warnings.append(f"STOP LOSS too far: {sl_distance_pct:.1f}%")
                    risk_score += 10
        
        else:  # SHORT
            entry_for_rr = (entry_zone_low + entry_zone_high) / 2
            distance_to_sl = abs(stop_loss - entry_for_rr)
            distances_to_targets = [abs(entry_for_rr - t) for t in targets]
            
            if distance_to_sl > 0:
                rr_ratios = [d / distance_to_sl for d in distances_to_targets]
                avg_rr = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0
                
                if avg_rr >= 2:
                    reasons.append(f"GOOD RR ratio: {avg_rr:.1f}:1")
                elif avg_rr >= 1.5:
                    reasons.append(f"ACCEPTABLE RR ratio: {avg_rr:.1f}:1")
                else:
                    warnings.append(f"POOR RR ratio: {avg_rr:.1f}:1")
                    risk_score += 20
        
        # 3. Check volume strength
        avg_volume = sum(volumes[-20:]) / 20 if volumes else 0
        current_volume = volumes[-1] if volumes else 0
        volume_strength = current_volume / avg_volume if avg_volume > 0 else 0
        
        if volume_strength < 0.7:
            warnings.append(f"LOW volume: {volume_strength:.2f}x average")
            risk_score += 10
        else:
            reasons.append(f"VOLUME confirmed: {volume_strength:.2f}x average")
        
        # 4. Check BTC dominance / market conditions
        # (In real system, would fetch BTC data and check correlation)
        
        # 5. Check funding rate status
        if funding:
            funding_rate = funding['funding_rate']
            if abs(funding_rate) > 0.001:  # > 0.1%
                warnings.append(f"ELEVATED funding rate: {funding['funding_rate_percent']:.3f}% (market overheated)")
                risk_score += 15
            else:
                reasons.append("Funding rate normal")
        
        # 6. Check resistance/support relationship
        sr = TechnicalIndicators.support_resistance(high_prices, low_prices)
        
        if direction == "LONG":
            if stop_loss < sr['primary_support'] * 0.98:
                reasons.append("Stop loss below key support (safer)")
            else:
                warnings.append("Stop loss not well placed")
                risk_score += 5
            
            # Check if entry zone is realistic
            if entry_zone_high > sr['primary_resistance']:
                warnings.append("Entry above resistance (risky)")
                risk_score += 10
        
        else:  # SHORT
            if stop_loss > sr['primary_resistance'] * 1.02:
                reasons.append("Stop loss above key resistance")
            else:
                warnings.append("Stop loss placement questionable")
                risk_score += 5
        
        # 7. Check RSI extremes
        current_rsi = rsi[-1] if rsi else None
        if current_rsi:
            if direction == "LONG" and current_rsi > 80:
                warnings.append(f"RSI overbought: {current_rsi:.1f} (potential pullback)")
                risk_score += 10
            elif direction == "SHORT" and current_rsi < 20:
                warnings.append(f"RSI oversold: {current_rsi:.1f} (potential bounce)")
                risk_score += 10
        
        # 8. Determine final status
        risk_percentage = (risk_score / max_risk) * 100
        
        if risk_percentage < 30:
            status = SignalValidity.VALID.value
            confidence = 85 + (30 - risk_percentage)
        elif risk_percentage < 50:
            status = SignalValidity.WAIT.value
            confidence = 70
        elif risk_percentage < 70:
            status = SignalValidity.RISKY.value
            confidence = 50
        else:
            status = SignalValidity.AVOID.value
            confidence = 30
        
        # 9. Suggested safer entry
        suggested_entry = entry_price
        if direction == "LONG":
            suggested_entry = sr['primary_support'] * 1.005
        else:
            suggested_entry = sr['primary_resistance'] * 0.995

        return {
            'status': status,
            'confidence': round(min(confidence, 100), 1),
            'risk_score': round(risk_percentage, 1),
            'rr_ratio': round(avg_rr, 2) if 'avg_rr' in locals() else 0,
            'trend_alignment': TechnicalIndicators.trend_score(ema8, ema34, [], [], close_prices)['direction'],
            'suggested_entry': round(suggested_entry, 6),
            'tp_levels': TechnicalIndicators.calculate_tp_levels(entry_price, stop_loss, direction),
            'reasons': reasons,
            'warnings': warnings,
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'targets': targets,
            'current_price': current_price,
            'volume_strength': round(volume_strength, 2),
            'rsi': round(current_rsi, 1) if current_rsi else None,
            'timeframe': timeframe
        }
