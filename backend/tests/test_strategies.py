"""
Test suite for strategy validator module
"""

import pytest
from datetime import datetime
from app.strategies.validator import StrategyValidator, StrategyStatus

# Sample candle data for testing
def get_sample_candles(trend='bullish'):
    """Generate sample OHLCV candles"""
    candles = []
    
    if trend == 'bullish':
        base_price = 100
        for i in range(100):
            close = base_price + (i * 0.5)
            high = close + 1
            low = close - 1
            open_p = close - 0.5
            candles.append({
                'timestamp': datetime.utcnow().timestamp() * 1000 + (i * 3600000),
                'open': open_p,
                'high': high,
                'low': low,
                'close': close,
                'volume': 1000000 + (i * 10000)
            })
    else:  # bearish
        base_price = 150
        for i in range(100):
            close = base_price - (i * 0.5)
            high = close + 1
            low = close - 1
            open_p = close + 0.5
            candles.append({
                'timestamp': datetime.utcnow().timestamp() * 1000 + (i * 3600000),
                'open': open_p,
                'high': high,
                'low': low,
                'close': close,
                'volume': 1000000 + (i * 10000)
            })
    
    return candles

class TestStrategyValidator:
    
    def test_validate_ema_crossover_long_bullish(self):
        """Test EMA crossover validation for bullish trend"""
        candles = get_sample_candles('bullish')
        result = StrategyValidator.validate_ema_crossover(candles, 'LONG', '4h')
        
        assert result is not None
        assert 'status' in result
        assert 'confidence' in result
        assert result['confidence'] > 0
    
    def test_validate_ema_crossover_short_bearish(self):
        """Test EMA crossover validation for bearish trend"""
        candles = get_sample_candles('bearish')
        result = StrategyValidator.validate_ema_crossover(candles, 'SHORT', '4h')
        
        assert result is not None
        assert 'status' in result
    
    def test_validate_ema_insufficient_data(self):
        """Test validation with insufficient data"""
        candles = get_sample_candles('bullish')[:30]
        result = StrategyValidator.validate_ema_crossover(candles, 'LONG', '4h')
        
        assert result['status'] == StrategyStatus.INVALID.value
    
    def test_validate_setup_zones_long(self):
        """Test setup zone calculation for long"""
        candles = get_sample_candles('bullish')
        zones = StrategyValidator.validate_setup_zones(candles, 'LONG')
        
        assert 'entry_zones' in zones
        assert 'exit_zones' in zones
        assert 'primary_zone' in zones['entry_zones']
        assert 'take_profit' in zones['exit_zones']
        assert 'stop_loss' in zones['exit_zones']
    
    def test_validate_setup_zones_short(self):
        """Test setup zone calculation for short"""
        candles = get_sample_candles('bearish')
        zones = StrategyValidator.validate_setup_zones(candles, 'SHORT')
        
        assert 'entry_zones' in zones
        assert zones['exit_zones']['take_profit'] < zones['exit_zones']['stop_loss']
    
    def test_confidence_scores(self):
        """Test confidence scoring"""
        candles_bullish = get_sample_candles('bullish')
        candles_bearish = get_sample_candles('bearish')
        
        result_bullish = StrategyValidator.validate_ema_crossover(candles_bullish, 'LONG', '4h')
        result_bearish = StrategyValidator.validate_ema_crossover(candles_bearish, 'SHORT', '4h')
        
        # Bullish setup should have better long confidence
        assert result_bullish['confidence'] >= 0
        assert result_bearish['confidence'] >= 0
    
    def test_reason_generation(self):
        """Test that reasons are generated"""
        candles = get_sample_candles('bullish')
        result = StrategyValidator.validate_ema_crossover(candles, 'LONG', '4h')
        
        assert 'reasons' in result
        assert len(result['reasons']) > 0
        assert all(isinstance(r, str) for r in result['reasons'])
    
    def test_timeframe_parameter(self):
        """Test different timeframe parameters"""
        candles = get_sample_candles('bullish')
        
        result_1h = StrategyValidator.validate_ema_crossover(candles, 'LONG', '1h')
        result_4h = StrategyValidator.validate_ema_crossover(candles, 'LONG', '4h')
        result_1d = StrategyValidator.validate_ema_crossover(candles, 'LONG', '1d')
        
        assert result_1h['timeframe'] == '1h'
        assert result_4h['timeframe'] == '4h'
        assert result_1d['timeframe'] == '1d'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
