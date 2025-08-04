from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.database import Base

class HistoricalData(Base):
    __tablename__ = "historical_data"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker_id = Column(Integer, ForeignKey("tickers.id"), nullable=False)
    date = Column(Date, nullable=False)
    open_price = Column(Float)
    close_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    volume = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    ticker = relationship("Ticker", back_populates="historical_data") 