from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=True)
    email = Column(String, unique=True, nullable=True)
    username = Column(String, unique=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    alerts_enabled = Column(Boolean, default=True)
    last_alert_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    queries = relationship("QueryHistory", back_populates="user")
    watchlists = relationship("Watchlist", back_populates="user")
    signals = relationship("SignalLog", back_populates="user")

class QueryHistory(Base):
    __tablename__ = "query_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query_type = Column(String)  # analyze, strategy, signal
    symbol = Column(String)
    timeframe = Column(String, nullable=True)
    query_params = Column(JSON)
    response = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="queries")

class Watchlist(Base):
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="watchlists")

class SignalLog(Base):
    __tablename__ = "signal_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String)
    direction = Column(String)  # LONG, SHORT
    entry_price = Column(Float)
    entry_zone_low = Column(Float)
    entry_zone_high = Column(Float)
    stop_loss = Column(Float)
    targets = Column(JSON)
    signal_status = Column(String)  # VALID, WAIT, AVOID
    reasoning = Column(Text)
    risk_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="signals")

class CacheData(Base):
    __tablename__ = "cache_data"
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True)
    value = Column(JSON)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
