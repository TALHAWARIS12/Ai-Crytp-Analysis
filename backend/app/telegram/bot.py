import logging
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.enums import ParseMode
import asyncio
from datetime import datetime
import re

from app.core.config import settings
from app.market_data.service import market_data_service
from app.strategies.validator import StrategyValidator
from app.strategies.signal_verifier import SignalVerifier
from app.ai.reasoning import AIReasoningEngine
from app.db.database import SessionLocal
from app.services.user_service import user_service
from app.services.signal_parser import signal_parser
import httpx

import socket
from aiohttp import TCPConnector

logger = logging.getLogger(__name__)

from aiogram.client.session.aiohttp import AiohttpSession
import aiohttp

# Force IPv4 + robust proxy support with lazy imports
class ResilientSession(AiohttpSession):
    """Session that handles DNS failures and proxy routing with lazy imports"""
    
    def __init__(self, proxy_url: str = None, **kwargs):
        super().__init__(**kwargs)
        self._proxy_url = proxy_url

    async def create_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = None
            
            if self._proxy_url:
                # Lazy import — works even if installed after first module load
                try:
                    from aiohttp_socks import ProxyConnector as _PC
                    
                    proxy_url = self._proxy_url
                    # Port 1080 is conventionally SOCKS5 — auto-detect
                    if proxy_url.startswith("http://") and ":1080" in proxy_url:
                        socks_url = proxy_url.replace("http://", "socks5://")
                        try:
                            connector = _PC.from_url(socks_url, family=socket.AF_INET)
                            logger.info(f"Using SOCKS5 proxy: {socks_url}")
                        except Exception:
                            pass
                    
                    if connector is None:
                        connector = _PC.from_url(proxy_url, family=socket.AF_INET)
                        logger.info(f"Using proxy: {proxy_url}")
                except ImportError:
                    logger.warning("aiohttp-socks not installed — proxy unavailable, using direct")
                except Exception as e:
                    logger.warning(f"Proxy connector error: {e}")
            
            if connector is None:
                # Use explicit DNS servers to bypass broken system DNS
                # Covers: Cloudflare WARP (127.0.2.2), Google (8.8.8.8), Cloudflare (1.1.1.1)
                try:
                    from aiohttp.resolver import AsyncResolver
                    resolver = AsyncResolver(nameservers=["8.8.8.8", "1.1.1.1", "127.0.2.2"])
                    connector = aiohttp.TCPConnector(family=socket.AF_INET, resolver=resolver)
                    logger.info("Using custom DNS resolver (8.8.8.8, 1.1.1.1, 127.0.2.2)")
                except Exception as e:
                    logger.warning(f"Custom DNS resolver failed ({e}), using system default")
                    connector = aiohttp.TCPConnector(family=socket.AF_INET)
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                json_serialize=self.json_dumps
            )
        return self._session


def _create_bot(proxy_url: str = None):
    """Create a Bot instance with optional proxy"""
    session = ResilientSession(proxy_url=proxy_url)
    return Bot(token=settings.telegram_bot_token, session=session)


# Initialize bot — use proxy from the start if configured
_proxy = settings.telegram_proxy if settings.telegram_proxy else None
bot = _create_bot(proxy_url=_proxy) if settings.telegram_bot_token and "your-" not in settings.telegram_bot_token else None
dp = Dispatcher()
router = Router()
dp.include_router(router)

class TelegramBot:
    """Premium Telegram bot interface for trading assistant"""
    
    @staticmethod
    def format_price(value: float) -> str:
        """Format price for readability"""
        if value < 1:
            return f"${value:.6f}"
        elif value < 100:
            return f"${value:.2f}"
        else:
            return f"${value:,.0f}"
    
    @staticmethod
    def format_analysis(data: dict) -> str:
        """Format analysis into readable Telegram message"""
        sr = data.get('sr', {})
        liquidity = data.get('liquidity', {})
        volume = data.get('volume', {})
        order_flow = data.get('order_flow', {})
        mtf = data.get('mtf', {})
        indicators = data.get('indicators', {})
        
        msg = f"""
🏛 <b>INSTITUTIONAL ANALYSIS: {data['symbol']}</b>
────────────────────
💰 <b>PRICE:</b> {TelegramBot.format_price(data['current_price'])}
🎯 <b>FINAL DECISION: {data['judgment']}</b>

📊 <b>TECHNICAL INDICATORS:</b>
• <b>EMA 8/34:</b> {TelegramBot.format_price(indicators.get('ema8', 0))} / {TelegramBot.format_price(indicators.get('ema34', 0))}
• <b>RSI (14):</b> {indicators.get('rsi', 'N/A')}
• <b>MA 50/200:</b> {TelegramBot.format_price(indicators.get('sma50', 0))} / {TelegramBot.format_price(indicators.get('sma200', 0))}

⏱ <b>MULTI-TIMEFRAME ANALYSIS:</b>""""""
        for tf in ['4h', '1h', '30m', '15m']:
            tf_data = mtf.get(tf, {})
            if tf_data:
                choch_str = f" | CHoCH: {tf_data.get('choch_type')}" if tf_data.get('choch_type') else ""
                msg += f"\n• <b>{tf.upper()}</b>: {tf_data.get('trend')} | Struct: {tf_data.get('structure')} | {tf_data.get('bos')}{choch_str}"

        msg += f"""

🧱 <b>SUPPORT & RESISTANCE:</b>
🔴 <b>Strong Res:</b> {', '.join(TelegramBot.format_price(r) for r in sr.get('strong_resistance', [])[:2]) if sr.get('strong_resistance') else 'N/A'}
🔸 <b>Weak Res:</b> {', '.join(TelegramBot.format_price(r) for r in sr.get('weak_resistance', [])[:2]) if sr.get('weak_resistance') else 'N/A'}
🟢 <b>Strong Sup:</b> {', '.join(TelegramBot.format_price(s) for s in sr.get('strong_support', [])[:2]) if sr.get('strong_support') else 'N/A'}
🔹 <b>Weak Sup:</b> {', '.join(TelegramBot.format_price(s) for s in sr.get('weak_support', [])[:2]) if sr.get('weak_support') else 'N/A'}

💧 <b>LIQUIDITY ZONES:</b>
• <b>Buy-side:</b> {', '.join(liquidity.get('buy_side', []))}
• <b>Sell-side:</b> {', '.join(liquidity.get('sell_side', []))}

📊 <b>VOLUME ANALYSIS:</b>
• {volume.get('message', 'N/A')}

🌊 <b>ORDER FLOW:</b>
• <b>Imbalance:</b> {order_flow.get('imbalance', 'N/A')}
• <b>Strong Bids:</b> {', '.join(TelegramBot.format_price(b) for b in order_flow.get('strong_bids', [])[:2]) if order_flow.get('strong_bids') else 'None'}
• <b>Heavy Asks:</b> {', '.join(TelegramBot.format_price(a) for a in order_flow.get('heavy_asks', [])[:2]) if order_flow.get('heavy_asks') else 'None'}

🧠 <b>AI REASONING:</b>
{data.get('analysis', 'Analysis unavailable')}
────────────────────
<i>Powered by AI Trading Assistant</i>
        """
        return msg.strip()
    
    @staticmethod
    def format_strategy(data: dict) -> str:
        """Format strategy validation into readable message"""
        status = data.get('status', 'INVALID')
        emoji = "✅" if "VALID" in status else "⏳" if "WAIT" in status else "❌"
        mtf = data.get('mtf', {})
        sr = data.get('sr', {})
        liquidity = data.get('liquidity', {})
        indicators = data.get('indicators', {})
        
        msg = f"""
🛡 <b>STRATEGY REPORT: {data.get('symbol', 'Unknown')}</b>
────────────────────
💰 <b>PRICE:</b> {TelegramBot.format_price(data.get('current_price', 0))}
{emoji} <b>DECISION: {status}</b>

📊 <b>TECHNICAL INDICATORS:</b>
• <b>EMA 8/34:</b> {TelegramBot.format_price(indicators.get('ema8', 0))} / {TelegramBot.format_price(indicators.get('ema34', 0))}
• <b>RSI (14):</b> {indicators.get('rsi', 'N/A')}
• <b>MA 50/200:</b> {TelegramBot.format_price(indicators.get('sma50', 0))} / {TelegramBot.format_price(indicators.get('sma200', 0))}

⏱ <b>MULTI-TIMEFRAME ANALYSIS:</b>"""
        for tf in ['4h', '1h', '30m', '15m']:
            tf_data = mtf.get(tf, {})
            if tf_data:
                choch_str = f" | CHoCH: {tf_data.get('choch_type')}" if tf_data.get('choch_type') else ""
                msg += f"\n• <b>{tf.upper()}</b>: {tf_data.get('trend')} | Struct: {tf_data.get('structure')} | {tf_data.get('bos')}{choch_str}"

        msg += f"""

📝 <b>STRATEGY CHECKLIST:</b>
{chr(10).join("• " + r for r in data.get('reasons', [])[:5])}

📉 <b>SETUP ZONES:</b>
• <b>Entry:</b> {TelegramBot.format_price(((data.get('entry_zones') or {}).get('primary_zone') or {}).get('low', 0)) if isinstance((data.get('entry_zones') or {}).get('primary_zone'), dict) else 'N/A'}
• <b>Take Profit:</b> {TelegramBot.format_price((data.get('exit_zones') or {}).get('take_profit', 0)) if isinstance(data.get('exit_zones'), dict) else 'N/A'}
• <b>Stop Loss:</b> {TelegramBot.format_price((data.get('exit_zones') or {}).get('stop_loss', 0)) if isinstance(data.get('exit_zones'), dict) else 'N/A'}

🧱 <b>SUPPORT & RESISTANCE:</b>
🟢 <b>Support:</b> {', '.join(TelegramBot.format_price(s) for s in sr.get('strong_support', [])[:2]) if sr.get('strong_support') else 'N/A'}
🔴 <b>Resistance:</b> {', '.join(TelegramBot.format_price(r) for r in sr.get('strong_resistance', [])[:2]) if sr.get('strong_resistance') else 'N/A'}

💧 <b>LIQUIDITY ZONES:</b>
• <b>Buy-side:</b> {', '.join(liquidity.get('buy_side', [])) if liquidity.get('buy_side') else 'None detected'}
• <b>Sell-side:</b> {', '.join(liquidity.get('sell_side', [])) if liquidity.get('sell_side') else 'None detected'}

🧠 <b>EXPERT VIEW:</b>
{data.get('ai_reasoning', 'Reasoning unavailable')}
────────────────────
<i>Powered by AI Trading Assistant</i>
        """
        return msg.strip()
    
    @staticmethod
    def format_signal(data: dict) -> str:
        """Format signal verification into readable message"""
        status = data.get('status', 'AVOID')
        status_emoji = "✅" if "VALID" in status else "⏳" if "WAIT" in status else "❌"
        msg = f"""
📡 <b>SIGNAL VERIFICATION: {data.get('symbol', 'Unknown')}</b>
────────────────────
{status_emoji} <b>STATUS: {status}</b>
⚖ <b>RR Ratio:</b> {data.get('rr_ratio', 'N/A')}:1
📊 <b>Risk Score:</b> {data['risk_score']:.0f}%
📈 <b>Trend:</b> {data.get('trend_alignment', 'N/A')}

🛠 <b>TRADE PARAMETERS:</b>
• <b>Direction:</b> {data['direction']}
• <b>Entry:</b> {TelegramBot.format_price(data['entry_price'])}
• <b>Stop Loss:</b> {TelegramBot.format_price(data['stop_loss'])}
• <b>Targets:</b> {', '.join(TelegramBot.format_price(t) for t in data.get('targets', []))}

💡 <b>TAKE PROFIT TARGETS:</b>
{chr(10).join(f"• TP{i+1}: {TelegramBot.format_price(tp)}" for i, tp in enumerate(data.get('tp_levels', [])))}

💡 <b>PRO ANALYSIS:</b>
{chr(10).join(f"• {r}" for r in data.get('reasons', [])[:3])}

{f"🚨 <b>WARNINGS:</b>{chr(10)}" + chr(10).join(f"⚠ {w}" for w in data.get('warnings', [])[:2]) if data.get('warnings') else ""}

🧠 <b>INSTITUTIONAL VIEW:</b>
{data.get('ai_reasoning', 'Analysis unavailable')}
────────────────────
        """
        return msg.strip()

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        return market_data_service._normalize_symbol(symbol)

    @staticmethod
    def parse_natural_language(text: str):
        content = text.strip().upper()
        # Avoid matching multi-line inputs as natural language commands
        if '\n' in text.strip():
            return None
            
        m = re.search(r"(?:ANALYZE|ANALYSIS)\s+([A-Z0-9/_-]+)", content)
        if m:
            return ("analyze", TelegramBot.normalize_symbol(m.group(1)))
        m = re.search(r"(?:LONG|SHORT)\s+([A-Z0-9/_-]+)", content)
        if m:
            direction = "LONG" if "LONG" in content else "SHORT"
            return ("strategy", TelegramBot.normalize_symbol(m.group(1)), direction, "4h")
        return None

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command"""
    welcome_msg = """
<b>Welcome to AI Crypto Trading Assistant</b>

I'm your premium institutional-grade trading analysis bot.

<b>Commands:</b>
/analyze BTCUSDT - Full coin analysis
/strategy BTCUSDT LONG 4H - Validate strategy setup
/checksignal - Verify your trading signal
/help - Show help

<b>Examples:</b>
/analyze ETHUSDT
/strategy BTCUSDT SHORT 1H

Always trade with discipline and risk management.
    """
    # Persist user
    with SessionLocal() as db:
        user_service.get_or_create_user(
            db, 
            telegram_id=str(message.from_user.id), 
            username=message.from_user.username
        )
    
    await message.reply(welcome_msg, parse_mode=ParseMode.HTML)

@router.message(Command("alerts"))
async def cmd_alerts(message: Message):
    """Handle /alerts on/off command"""
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /alerts on OR /alerts off", parse_mode=ParseMode.HTML)
        return
    
    action = args[1].lower()
    enabled = action == "on"
    
    with SessionLocal() as db:
        success = user_service.toggle_alerts(db, str(message.from_user.id), enabled)
        if success:
            status = "enabled" if enabled else "disabled"
            await message.reply(f"✅ Proactive alerts {status} successfully.", parse_mode=ParseMode.HTML)
        else:
            await message.reply("❌ Error updating alert preferences. Use /start first.", parse_mode=ParseMode.HTML)

@router.message(Command("topgainers"))
async def cmd_topgainers(message: Message):
    """Handle /topgainers command"""
    try:
        await message.reply("🔄 Fetching top gainers...", parse_mode=ParseMode.HTML)
        sorted_tickers = await market_data_service.get_top_gainers(10)
        
        if not sorted_tickers:
            await message.reply("❌ Error fetching top gainers. Market might be restricted.", parse_mode=ParseMode.HTML)
            return

        msg = "<b>🔥 Top 10 Gainers (24h)</b>\n\n"
        for i, t in enumerate(sorted_tickers):
            change = t.get('percentage', 0) or 0
            msg += f"{i+1}. <b>{t['symbol']}</b>: +{change:.2f}%\n"
        
        await message.reply(msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Top gainers error: {str(e)}")
        await message.reply("❌ Error fetching top gainers.", parse_mode=ParseMode.HTML)

@router.message(Command("feargreed"))
async def cmd_feargreed(message: Message):
    """Handle /feargreed command"""
    try:
        from app.utils.http import http_client
        client = http_client.get_client()
        resp = await client.get("https://api.alternative.me/fng/", timeout=10)
        if resp.status_code == 200:
            data = resp.json()['data'][0]
            value = data['value']
            classification = data['value_classification']
            
            msg = f"<b>📊 Fear & Greed Index</b>\n\nValue: <b>{value}</b>\nClassification: <b>{classification}</b>"
            await message.reply(msg, parse_mode=ParseMode.HTML)
        else:
            await message.reply("❌ Error fetching Fear & Greed index.", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"FearGreed error: {str(e)}")
        await message.reply("❌ Error fetching index.", parse_mode=ParseMode.HTML)

@router.message(Command("ema"))
async def cmd_ema(message: Message):
    """Handle /ema command - Quick EMA check"""
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Usage: /ema BTCUSDT", parse_mode=ParseMode.HTML)
        return
    
    symbol = TelegramBot.normalize_symbol(args[1])
    await message.reply(f"🔄 Fetching EMA for {symbol}...", parse_mode=ParseMode.HTML)
    
    try:
        candles = await market_data_service.get_ohlcv(symbol, '4h', 100)
        if not candles:
            await message.reply("❌ Could not fetch data.", parse_mode=ParseMode.HTML)
            return
            
        from app.indicators.technical import TechnicalIndicators
        close_prices = [c['close'] for c in candles]
        ema8 = TechnicalIndicators.ema(close_prices, 8)
        ema34 = TechnicalIndicators.ema(close_prices, 34)
        sma200 = TechnicalIndicators.sma(close_prices, 200)
        
        msg = f"""
<b>{symbol} EMA Analysis (4H)</b>

Price: {TelegramBot.format_price(close_prices[-1])}
EMA 8: {TelegramBot.format_price(ema8[-1])}
EMA 34: {TelegramBot.format_price(ema34[-1])}
MA 200: {TelegramBot.format_price(sma200[-1]) if sma200[-1] else 'N/A'}

<b>Alignment:</b> {"🟢 BULLISH" if ema8[-1] > ema34[-1] else "🔴 BEARISH"}
        """
        await message.reply(msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"EMA error: {str(e)}")
        await message.reply("❌ Error calculating EMA.", parse_mode=ParseMode.HTML)

@router.message(Command("signalcheck"))
async def cmd_signalcheck(message: Message):
    """Alias for /checksignal"""
    await cmd_checksignal(message)

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_msg = """
<b>AI Crypto Trading Assistant - Help</b>

<b>/analyze [SYMBOL]</b>
Full coin analysis with technical indicators, support/resistance, and AI reasoning.
Example: <code>/analyze BTCUSDT</code>

<b>/strategy [SYMBOL] [DIRECTION] [TIMEFRAME]</b>
Validate strategy setup against real market data.
Example: <code>/strategy ETH LONG 4H</code>

<b>/signalcheck</b>
Verify a trading signal you received. (Alias: /checksignal)
Provide entry, stops, targets in the next message.

<b>/alerts [on/off]</b>
Enable or disable proactive institutional market alerts.

<b>/topgainers</b>
See the top 10 market gainers in the last 24 hours.

<b>/feargreed</b>
Get the current Crypto Fear & Greed Index status.

<b>/ema [SYMBOL]</b>
Quick technical check (EMA 8/34 alignment + MA200).

<b>Features:</b>
✓ Real live market data from Binance Futures
✓ Proactive background monitoring (EMA crosses, breakouts, reversal zones)
✓ AI-powered institutional reasoning layer
✓ Risk assessment and RR ratio scoring
✓ Funding rate and Volume monitoring

<b>Remember:</b>
This tool provides ANALYSIS ONLY - no automated trading.
Always use proper risk management and position sizing.
    """
    await message.reply(help_msg, parse_mode=ParseMode.HTML)

@router.message(Command("analyze"))
async def cmd_analyze(message: Message):
    """Handle /analyze command"""
    try:
        args = message.text.split()
        
        if len(args) < 2:
            await message.reply("Usage: /analyze BTCUSDT", parse_mode=ParseMode.HTML)
            return
        
        symbol = TelegramBot.normalize_symbol(args[1])
        
        # Validate symbol
        valid = await market_data_service.validate_symbol(symbol)
        if not valid:
            await message.reply(f"<b>⚠ Symbol not found:</b> {symbol}", parse_mode=ParseMode.HTML)
            return
        
        # Fetch market data
        await message.reply("🔄 Performing Institutional Analysis...", parse_mode=ParseMode.HTML)
        
        market_data = await market_data_service.get_full_market_snapshot(symbol)
        mtf_data = await market_data_service.get_multi_timeframe_data(symbol, ['15m', '30m', '1h', '4h'])
        
        if not market_data['candles']:
            await message.reply("❌ Unable to fetch market data", parse_mode=ParseMode.HTML)
            return
            
        from app.indicators.technical import TechnicalIndicators
        
        analysis_data = {
            'symbol': symbol,
            'current_price': market_data['ticker']['last'] if market_data.get('ticker') else 0,
            'funding_rate': market_data['funding_rate'],
            'mtf': {},
            'liquidity': {},
            'volume': {},
            'order_flow': {},
            'judgment': 'WAIT',
            'trend': 'NEUTRAL',
            'support': 0,
            'resistance': 0
        }
        
        # Multi-timeframe processing
        for tf in ['15m', '30m', '1h', '4h']:
            candles = mtf_data.get(tf, [])
            if not candles: continue
            
            close_prices = [c['close'] for c in candles]
            high_prices = [c['high'] for c in candles]
            low_prices = [c['low'] for c in candles]
            
            ema8 = TechnicalIndicators.ema(close_prices, 8)
            ema34 = TechnicalIndicators.ema(close_prices, 34)
            sma50 = TechnicalIndicators.sma(close_prices, 50)
            sma200 = TechnicalIndicators.sma(close_prices, 200)
            
            trend_score = TechnicalIndicators.trend_score(ema8, ema34, sma50, sma200, close_prices)
            structure = TechnicalIndicators.detect_structure(high_prices, low_prices, close_prices)
            
            analysis_data['mtf'][tf] = {
                'trend': trend_score['direction'],
                'structure': structure['structure'],
                'bos': f"BOS {structure['bos_direction']}" if structure['bos'] else "None",
                'choch': structure.get('choch'),
                'choch_type': structure.get('choch_type')
            }
            
            if tf == '4h':
                # Indicators
                analysis_data['indicators'] = {
                    'ema8': ema8[-1],
                    'ema34': ema34[-1],
                    'sma50': sma50[-1],
                    'sma200': sma200[-1],
                    'rsi': TechnicalIndicators.rsi(close_prices, 14)[-1] if len(close_prices) > 14 else 'N/A'
                }
                # Advanced S&R
                analysis_data['sr'] = TechnicalIndicators.support_resistance_advanced(high_prices, low_prices, close_prices)
                
                # Liquidity
                analysis_data['liquidity'] = TechnicalIndicators.detect_liquidity_zones(high_prices, low_prices)
                
                # Volume
                volumes = [c['volume'] for c in candles]
                analysis_data['volume'] = TechnicalIndicators.volume_analysis(volumes, close_prices)
                
                # Backwards compatibility for AI reasoning
                analysis_data['trend'] = trend_score['direction']
                analysis_data['support'] = analysis_data['sr']['primary_support']
                analysis_data['resistance'] = analysis_data['sr']['primary_resistance']
                
                # Calculate final judgment bias
                bullish_count = sum(1 for data in analysis_data['mtf'].values() if data['trend'] == 'BULLISH')
                bearish_count = sum(1 for data in analysis_data['mtf'].values() if data['trend'] == 'BEARISH')
                
                if bullish_count >= 3 and analysis_data['volume']['buyers_active']:
                    analysis_data['judgment'] = 'LONG BIAS'
                elif bearish_count >= 3 and analysis_data['volume']['sellers_active']:
                    analysis_data['judgment'] = 'SHORT BIAS'
                elif bullish_count >= 3:
                    analysis_data['judgment'] = 'WEAK LONG'
                elif bearish_count >= 3:
                    analysis_data['judgment'] = 'WEAK SHORT'
                else:
                    analysis_data['judgment'] = 'WAIT / AVOID'

        # Order Flow Analysis
        analysis_data['order_flow'] = TechnicalIndicators.analyze_order_book(market_data.get('order_book', {}))
        
        # Get AI analysis
        analysis_data['analysis'] = await AIReasoningEngine.analyze_coin(analysis_data)
        
        result = TelegramBot.format_analysis(analysis_data)
        await message.reply(result, parse_mode=ParseMode.HTML)
    
    except Exception as e:
        logger.error(f"SignalParser error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await message.reply(f"❌ Error: {str(e)}", parse_mode=ParseMode.HTML)

@router.message(Command("strategy"))
async def cmd_strategy(message: Message):
    """Handle /strategy command"""
    try:
        args = message.text.split()
        
        if len(args) < 4:
            await message.reply(
                "Usage: /strategy BTCUSDT LONG 4H",
                parse_mode=ParseMode.HTML
            )
            return
        
        symbol = TelegramBot.normalize_symbol(args[1])
        
        direction = args[2].upper()
        timeframe = args[3].lower()
        
        if direction not in ['LONG', 'SHORT']:
            await message.reply("Direction must be LONG or SHORT", parse_mode=ParseMode.HTML)
            return
        
        # ── Step 1: Perform Full Institutional Analysis ──
        market_data = await market_data_service.get_full_market_snapshot(symbol)
        mtf_data = await market_data_service.get_multi_timeframe_data(symbol, ['15m', '30m', '1h', '4h'])
        
        if not market_data['candles']:
            await message.reply("❌ Unable to fetch market data", parse_mode=ParseMode.HTML)
            return

        from app.indicators.technical import TechnicalIndicators
        
        # Prepare full analysis data
        analysis_data = {
            'symbol': symbol,
            'current_price': market_data['ticker']['last'] if market_data.get('ticker') else 0,
            'funding_rate': market_data['funding_rate'],
            'mtf': {},
            'indicators': {},
            'liquidity': {},
            'volume': {},
            'order_flow': {},
            'judgment': 'WAIT',
            'trend': 'NEUTRAL'
        }

        # Process all timeframes
        for tf_val in ['15m', '30m', '1h', '4h']:
            candles_tf = mtf_data.get(tf_val, [])
            if not candles_tf: continue
            
            closes = [c['close'] for c in candles_tf]
            highs = [c['high'] for c in candles_tf]
            lows = [c['low'] for c in candles_tf]
            
            e8 = TechnicalIndicators.ema(closes, 8)
            e34 = TechnicalIndicators.ema(closes, 34)
            s50 = TechnicalIndicators.sma(closes, 50)
            s200 = TechnicalIndicators.sma(closes, 200)
            
            struct = TechnicalIndicators.detect_structure(highs, lows, closes)
            analysis_data['mtf'][tf_val] = {
                'trend': TechnicalIndicators.trend_score(e8, e34, s50, s200, closes)['direction'],
                'structure': struct['structure'],
                'bos': f"BOS {struct['bos_direction']}" if struct['bos'] else "None",
                'choch_type': struct.get('choch_type')
            }
            
            if tf_val == '4h':
                analysis_data['indicators'] = {
                    'ema8': e8[-1], 'ema34': e34[-1], 'sma50': s50[-1], 'sma200': s200[-1],
                    'rsi': TechnicalIndicators.rsi(closes, 14)[-1] if len(closes) > 14 else 'N/A'
                }
                analysis_data['sr'] = TechnicalIndicators.support_resistance_advanced(highs, lows, closes)
                analysis_data['liquidity'] = TechnicalIndicators.detect_liquidity_zones(highs, lows)
                analysis_data['volume'] = TechnicalIndicators.volume_analysis([c['volume'] for c in candles_tf], closes)

        # Order Flow
        analysis_data['order_flow'] = TechnicalIndicators.analyze_order_book(market_data.get('order_book', {}))
        
        # ── Step 2: Validate Specific Strategy ──
        target_candles = mtf_data.get(timeframe, [])
        if not target_candles:
             target_candles = await market_data_service.get_ohlcv(symbol, timeframe, 100)

        strat_result = await StrategyValidator.validate_ema_crossover(symbol, target_candles, direction, timeframe)
        zones = StrategyValidator.validate_setup_zones(target_candles, direction)
        
        # Merge data
        analysis_data.update({
            'status': strat_result['status'],
            'confidence': strat_result['confidence'],
            'reasons': strat_result['reasons'],
            'entry_zones': zones.get('entry_zones'),
            'exit_zones': zones.get('exit_zones')
        })
        
        # Get AI reasoning
        analysis_data['ai_reasoning'] = await AIReasoningEngine.validate_strategy_reasoning(analysis_data)
        
        formatted = TelegramBot.format_strategy(analysis_data)
        await message.reply(formatted, parse_mode=ParseMode.HTML)
    
    except Exception as e:
        logger.error(f"Strategy error: {str(e)}")
        await message.reply(f"❌ Error: {str(e)}", parse_mode=ParseMode.HTML)

@router.message(Command("checksignal"))
async def cmd_checksignal(message: Message):
    """Handle /checksignal command - interactive signal verification"""
    await message.reply(
        """<b>Signal Checker</b>

Please provide your signal in this format:

SYMBOL DIRECTION
Entry1 X-Y
Entry2 Z
Current CMP
Targets T1, T2, T3
SL STOPLOSS

Example:

RAREUSDT LONG
Entry 0.0179-0.0180
Current 0.0179
Targets 0.0250, 0.0300
SL 0.0161

Send your signal in the next message.""",
        parse_mode=ParseMode.HTML
    )

@router.message()
async def handle_signal_input(message: Message):
    """Handle signal input for verification"""
    try:
        text = (message.text or "").strip()
        if not text:
            return

        # 1. First, check if it's a structured trading signal (Highest priority)
        if len(text.split('\n')) >= 2 or any(k in text.upper() for k in ["ENTRY:", "TP:", "SL:", "TARGET:"]):
            parsed = signal_parser.parse(text)
            if parsed:
                symbol = TelegramBot.normalize_symbol(parsed['symbol'])
                direction = parsed['direction']
                
                # Get ticker for current price
                ticker = await market_data_service.get_ticker(symbol)
                if not ticker:
                    await message.reply(f"❌ Symbol not found: {symbol}", parse_mode=ParseMode.HTML)
                    return
                
                await message.reply("🔄 Checking signal against live institutional data...", parse_mode=ParseMode.HTML)
                
                # Verify
                result = await SignalVerifier.verify_signal(
                    symbol=symbol,
                    direction=direction,
                    entry_price=parsed['entry_price'],
                    entry_zone_low=parsed['entry_price'] * 0.995,
                    entry_zone_high=parsed['entry_price'] * 1.005,
                    targets=parsed['targets'],
                    stop_loss=parsed['stop_loss'],
                    current_price=ticker['last'],
                    timeframe='4h'
                )
                
                result['ai_reasoning'] = await AIReasoningEngine.evaluate_signal(result)
                
                formatted = TelegramBot.format_signal(result)
                await message.reply(formatted, parse_mode=ParseMode.HTML)
                return
            else:
                # If it looked like a signal (multi-line) but parsing failed
                if len(text.split('\n')) >= 3 and any(k in text.upper() for k in ["ENTRY", "TP", "SL", "TARGET"]):
                    await message.reply("❌ <b>Signal Parsing Failed</b>\n\nPlease ensure your signal follows the format:\n<code>SYMBOL DIRECTION\nEntry: X\nTargets: Y\nSL: Z</code>", parse_mode=ParseMode.HTML)
                    return

        # 2. Then check for Natural Language commands (e.g. "analyze btc")
        nl = TelegramBot.parse_natural_language(text)
        if nl:
            if nl[0] == "analyze":
                message.text = f"/analyze {nl[1]}"
                await cmd_analyze(message)
                return
            if nl[0] == "strategy":
                _, symbol, direction, timeframe = nl
                message.text = f"/strategy {symbol} {direction} {timeframe}"
                await cmd_strategy(message)
                return
        
        # 3. Last resort: check if it's just a single word coin name
        if len(text.split()) == 1 and len(text) < 10 and text.isalnum():
             await message.reply(f"I didn't recognize that signal. If you want to analyze {text.upper()}, use <code>/analyze {text.upper()}</code>", parse_mode=ParseMode.HTML)
    
    except Exception as e:
        logger.error(f"Signal parsing error: {str(e)}")

async def _test_bot_connection(test_bot) -> bool:
    """Quick connectivity test — try get_me() with 10s timeout"""
    try:
        me = await asyncio.wait_for(test_bot.get_me(), timeout=10)
        logger.info(f"✅ Connected to Telegram as @{me.username}")
        return True
    except Exception as e:
        logger.warning(f"Connection test failed: {e}")
        return False


async def run_bot():
    """Run the Telegram bot with smart connectivity detection and proxy fallback"""
    global bot
    
    if not bot:
        logger.warning("Bot not initialized.")
        return
        
    logger.info("Starting Telegram bot...")
    
    # ── Phase 1: Find a working connection strategy ──
    # Build strategies: proxy first (if configured), then direct
    strategies = []
    if settings.telegram_proxy:
        proxy = settings.telegram_proxy
        # Port 1080 is conventionally SOCKS5 — try that first
        if proxy.startswith("http://") and ":1080" in proxy:
            strategies.append(("socks5", proxy.replace("http://", "socks5://")))
        strategies.append(("proxy", proxy))
    strategies.append(("direct", None))
    
    connected = False
    for name, proxy_url in strategies:
        logger.info(f"Testing {name} connection{f' via {proxy_url}' if proxy_url else ''}...")
        test_bot = _create_bot(proxy_url=proxy_url)
        
        if await _test_bot_connection(test_bot):
            bot = test_bot
            connected = True
            break
        else:
            # Clean up failed session
            try:
                await test_bot.session.close()
            except Exception:
                pass
    
    if not connected:
        logger.error("❌ All connection strategies failed. Telegram bot disabled.")
        logger.error("Check: VPN active? Proxy running on 127.0.0.1:1080? DNS working?")
        return
    
    # ── Phase 2: Run polling with retry ──
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Starting polling (attempt {attempt}/{max_retries})...")
            await dp.start_polling(bot, timeout=60)
            break  # Clean exit
            
        except Exception as e:
            logger.error(f"Polling error (attempt {attempt}): {e}")
            
            if bot.session:
                try:
                    await bot.session.close()
                except Exception:
                    pass
            
            if attempt == max_retries:
                logger.error("Telegram bot failed after max retries. Disabling gracefully.")
                return
            
            # Recreate bot with same strategy that worked
            bot = _create_bot(proxy_url=strategies[0][1] if settings.telegram_proxy else None)
            
            delay = min(5 * (2 ** (attempt - 1)), 60)
            logger.info(f"Waiting {delay}s before retry...")
            await asyncio.sleep(delay)
    
    logger.info("Bot polling stopped.")
