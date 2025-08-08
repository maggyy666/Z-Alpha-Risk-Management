from sqlalchemy import Column, Integer, String, Float, DateTime, Date
from sqlalchemy.sql import func
from database.database import Base

class BidAskData(Base):
    __tablename__ = "bid_ask_data"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker_symbol = Column(String(10), nullable=False, index=True)  # e.g., "AAPL", "AMD"
    date = Column(Date, nullable=False)
    bid_price = Column(Float)
    ask_price = Column(Float)
    spread_pct = Column(Float)  # Calculated spread percentage
    volume = Column(Integer)  # Current volume for context
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Composite index for efficient queries
    __table_args__ = (
        # This will be added in the database creation
    )
