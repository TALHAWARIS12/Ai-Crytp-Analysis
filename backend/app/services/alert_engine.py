import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import User
from app.market_data.service import market_data_service
from app.indicators.technical import TechnicalIndicators
from app.services.user_service import user_service
from app.telegram.bot import bot, TelegramBot
from aiogram.enums import ParseMode

logger = logging.getLogger(__name__)

class AlertEngine:
    """Proactive alerts engine for market monitoring"""
    
    WATCHLIST = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT"]
    COOLDOWN_MINUTES = 60

    def __init__(self):
        self.last_alerts = {} # symbol -> {condition -> timestamp}

    async def run_check(self):
        """Perform a single pass of market checks"""
        logger.info("Alert Engine: Starting market check...")
        
        for symbol in self.WATCHLIST:
            try:
                await self._check_symbol(symbol)
                # Sleep between symbols to respect rate limits
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Alert Engine: Error checking {symbol}: {e}")

    async def _check_symbol(self, symbol: str):
        # Fetch data
        candles_1h = await market_data_service.get_ohlcv(symbol, '1h', 50)
        funding = await market_data_service.get_funding_rate(symbol)
        
        if not candles_1h:
            return

        close_prices = [c['close'] for c in candles_1h]
        high_prices = [c['high'] for c in candles_1h]
        low_prices = [c['low'] for c in candles_1h]
        volumes = [c['volume'] for c in candles_1h]
        
        ema8 = TechnicalIndicators.ema(close_prices, 8)
        ema34 = TechnicalIndicators.ema(close_prices, 34)
        rsi = TechnicalIndicators.rsi(close_prices, 14)
        
        current_price = close_prices[-1]
        prev_ema8 = ema8[-2]
        prev_ema34 = ema34[-2]
        curr_ema8 = ema8[-1]
        curr_ema34 = ema34[-1]
        curr_rsi = rsi[-1]
        
        alerts = []

        # 1. EMA Cross
        if prev_ema8 <= prev_ema34 and curr_ema8 > curr_ema34:
            alerts.append({
                'id': 'ema_cross_up',
                'title': '🚀 Bullish EMA Cross (8/34)',
                'message': f"EMA 8 has crossed ABOVE EMA 34 on 1H timeframe."
            })
        elif prev_ema8 >= prev_ema34 and curr_ema8 < curr_ema34:
            alerts.append({
                'id': 'ema_cross_down',
                'title': '⚠️ Bearish EMA Cross (8/34)',
                'message': f"EMA 8 has crossed BELOW EMA 34 on 1H timeframe."
            })

        # 2. RSI Extreme
        if curr_rsi > 80:
            alerts.append({
                'id': 'rsi_overbought',
                'title': '🔥 RSI Overbought',
                'message': f"RSI is extremely high at {curr_rsi:.1f}. Potential pullback ahead."
            })
        elif curr_rsi < 20:
            alerts.append({
                'id': 'rsi_oversold',
                'title': '❄️ RSI Oversold',
                'message': f"RSI is extremely low at {curr_rsi:.1f}. Potential bounce ahead."
            })

        # 3. Volume Breakout
        avg_vol = sum(volumes[-21:-1]) / 20
        curr_vol = volumes[-1]
        if curr_vol > avg_vol * 3:
            alerts.append({
                'id': 'volume_spike',
                'title': '📊 Volume Spike',
                'message': f"Volume is {curr_vol/avg_vol:.1f}x higher than 20-period average."
            })

        # 4. Open Interest Spike
        oi_data = await market_data_service.get_open_interest(symbol)
        if oi_data:
            # Note: We need historical OI to detect spikes. 
            # For now, let's just log it or if we have a way to get history.
            # CCXT fetchOpenInterestHistory is available for some exchanges.
            pass

        # 5. Funding Extreme
        if funding and abs(funding['funding_rate']) > 0.001:
            alerts.append({
                'id': 'funding_extreme',
                'title': '💸 Funding Extreme',
                'message': f"Funding rate is overheated at {funding['funding_rate_percent']:.4f}%."
            })

        # 6. Strong Reversal Zone
        sr = TechnicalIndicators.support_resistance(high_prices, low_prices)
        if curr_rsi < 30 and current_price <= sr['primary_support'] * 1.01:
            alerts.append({
                'id': 'reversal_zone_long',
                'title': '🛡️ Strong Reversal Zone (Long)',
                'message': f"Price at support ({TelegramBot.format_price(sr['primary_support'])}) with oversold RSI ({curr_rsi:.1f})."
            })
        elif curr_rsi > 70 and current_price >= sr['primary_resistance'] * 0.99:
            alerts.append({
                'id': 'reversal_zone_short',
                'title': '🛡️ Strong Reversal Zone (Short)',
                'message': f"Price at resistance ({TelegramBot.format_price(sr['primary_resistance'])}) with overbought RSI ({curr_rsi:.1f})."
            })

        # Send alerts if any and not in cooldown
        for alert in alerts:
            if self._is_in_cooldown(symbol, alert['id']):
                continue
            
            await self._broadcast_alert(symbol, current_price, alert)
            self._update_cooldown(symbol, alert['id'])

    def _is_in_cooldown(self, symbol: str, alert_id: str) -> bool:
        key = f"{symbol}_{alert_id}"
        last_time = self.last_alerts.get(key)
        if not last_time:
            return False
        
        return datetime.utcnow() - last_time < timedelta(minutes=self.COOLDOWN_MINUTES)

    def _update_cooldown(self, symbol: str, alert_id: str):
        key = f"{symbol}_{alert_id}"
        self.last_alerts[key] = datetime.utcnow()

    async def _broadcast_alert(self, symbol: str, price: float, alert: Dict):
        if not bot:
            return

        with SessionLocal() as db:
            users = user_service.get_alert_recipients(db)
            if not users:
                return

            msg = f"""
<b>{alert['title']}</b>

<b>Symbol:</b> {symbol}
<b>Price:</b> {TelegramBot.format_price(price)}

{alert['message']}

<i>Sent by Institutional AI Monitoring</i>
            """
            
            for user in users:
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=msg,
                        parse_mode=ParseMode.HTML
                    )
                    user_service.update_last_alert_time(db, user.id)
                    # Slight delay between users to avoid Telegram rate limits
                    await asyncio.sleep(0.05)
                except Exception as e:
                    logger.warning(f"Failed to send alert to {user.telegram_id}: {e}")

alert_engine = AlertEngine()
