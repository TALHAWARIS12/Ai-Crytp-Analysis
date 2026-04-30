from app.telegram.bot import TelegramBot


def test_normalize_symbol_for_telegram():
    assert TelegramBot.normalize_symbol("BTCUSDT") == "BTC/USDT"
    assert TelegramBot.normalize_symbol("ethusdt") == "ETH/USDT"
    assert TelegramBot.normalize_symbol("SOL/USDT") == "SOL/USDT"


def test_natural_language_analyze_parse():
    parsed = TelegramBot.parse_natural_language("Analyze btcusdt now")
    assert parsed is not None
    assert parsed[0] == "analyze"
    assert parsed[1] == "BTC/USDT"


def test_natural_language_strategy_parse():
    parsed = TelegramBot.parse_natural_language("should i long ethusdt?")
    assert parsed is not None
    assert parsed[0] == "strategy"
    assert parsed[1] == "ETH/USDT"
    assert parsed[2] == "LONG"
