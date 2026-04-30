import pytest
from app.services.signal_parser import signal_parser

def test_parse_simple_signal():
    text = "BUY BTC 94300 TP 95000 SL 93800"
    result = signal_parser.parse(text)
    assert result is not None
    assert result['symbol'] == "BTC"
    assert result['direction'] == "LONG"
    assert result['entry_price'] == 94300
    assert result['stop_loss'] == 93800
    assert 95000 in result['targets']

def test_parse_formatted_signal():
    text = """
    SOL/USDT SHORT
    Entry: 145.50
    Targets: 140, 135, 130
    SL: 152
    """
    result = signal_parser.parse(text)
    assert result is not None
    assert result['symbol'] == "SOLUSDT"
    assert result['direction'] == "SHORT"
    assert result['entry_price'] == 145.50
    assert result['stop_loss'] == 152.0
    assert len(result['targets']) == 3
    assert 140.0 in result['targets']

def test_parse_invalid_text():
    text = "Hello world, this is not a signal"
    result = signal_parser.parse(text)
    assert result is None

def test_parse_missing_sl():
    text = "BUY BTC 90000 TP 95000"
    result = signal_parser.parse(text)
    assert result is None
