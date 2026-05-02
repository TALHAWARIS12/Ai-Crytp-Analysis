import re
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

class SignalParser:
    """Robust regex-based parser for trading signals"""
    
    @staticmethod
    def parse(text: str) -> Optional[Dict]:
        """
        Parses text like:
        BUY BTC 94300 TP 95000 SL 93800
        OR
        BTC/USDT LONG
        Entry: 65000
        Targets: 68000, 70000
        SL: 63000
        """
        try:
            content = text.upper().strip()
            # Remove common prefixes
            content = re.sub(r'^(?:SIGNAL|NEW SIGNAL|🚨|🔥|💎)\s*:?', '', content).strip()
            
            # 1. Extract Symbol
            # Prioritize symbols with quote currencies or specific length and context
            keywords = ["BUY", "SELL", "LONG", "SHORT", "SIGNAL", "ENTRY", "TARGET", "STOP", "SL", "TP"]
            
            # Look for symbols like BTC/USDT or BTCUSDT
            # Pattern: base symbol (2-6 chars) followed by optional quote
            symbol_match = re.search(r'([A-Z0-9]{2,6}(?:[/-]?(?:USDT|USDC|BUSD|BTC|ETH))|(?:\b[A-Z0-9]{2,6}\b))', content)
            
            symbol = None
            if symbol_match:
                # Iterate matches to find one that isn't a keyword
                matches = re.finditer(r'([A-Z0-9]{2,10}(?:[/-]?(?:USDT|USDC|BUSD|BTC|ETH))?)', content)
                for m in matches:
                    potential = m.group(1).replace('/', '').replace('-', '')
                    if potential not in keywords and len(potential) >= 2:
                        symbol = potential
                        break
            
            if not symbol:
                return None
            
            # 2. Extract Direction
            direction = None
            if any(word in content for word in ["BUY", "LONG", "BULLISH"]):
                direction = "LONG"
            elif any(word in content for word in ["SELL", "SHORT", "BEARISH"]):
                direction = "SHORT"
            
            if not direction:
                return None
                
            # 3. Extract Entry Price
            entry_match = re.search(r'(?:ENTRY|ENTRIES|AT|@)\s*:?\s*(\d+(?:\.\d+)?)', content)
            if not entry_match:
                # Try just finding numbers after direction/symbol
                nums = re.findall(r'(\d+(?:\.\d+)?)', content)
                if nums:
                    entry_price = float(nums[0])
                else:
                    return None
            else:
                entry_price = float(entry_match.group(1))

            # 4. Extract Stop Loss
            sl_match = re.search(r'(?:SL|STOP|STOPLOSS)\s*:?\s*(\d+(?:\.\d+)?)', content)
            stop_loss = float(sl_match.group(1)) if sl_match else None
            
            # 5. Extract Targets
            tp_match = re.search(r'(?:TP|TARGETS?|EXIT)\s*:?\s*([\d\s\.,]+)', content)
            targets = []
            if tp_match:
                tp_text = tp_match.group(1)
                # Find all numbers in the TP section
                tp_nums = re.findall(r'(\d+(?:\.\d+)?)', tp_text)
                targets = [float(n) for n in tp_nums]
            
            if not targets and not stop_loss:
                # Maybe they are just space separated
                nums = re.findall(r'(\d+(?:\.\d+)?)', content)
                # If we have at least 3 numbers: entry, tp1, sl
                if len(nums) >= 3:
                    # Very risky guessing, but let's try
                    pass
            
            if not stop_loss or not targets:
                return None
                
            return {
                'symbol': symbol,
                'direction': direction,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'targets': targets
            }
            
        except Exception as e:
            logger.error(f"SignalParser error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

signal_parser = SignalParser()
