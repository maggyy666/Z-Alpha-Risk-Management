from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.database import Base

class Ticker(Base):
    __tablename__ = "tickers"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, index=True, nullable=False)
    company_name = Column(String(200))
    sector = Column(String(100))
    market_cap = Column(Float)
    last_price = Column(Float)
    volume = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    historical_data = relationship("HistoricalData", back_populates="ticker")

class TickerInfo(Base):
    __tablename__ = "ticker_info"
    
    symbol = Column(String(10), primary_key=True, index=True)
    industry = Column(String(100))
    sector = Column(String(100))
    market_cap = Column(Float)  # w USD
    company_name = Column(String(200))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) 