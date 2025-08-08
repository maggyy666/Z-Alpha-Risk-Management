from sqlalchemy import Column, Integer, String, Float, DateTime, Date
from sqlalchemy.sql import func
from database.database import Base

class TickerData(Base):
    __tablename__ = "ticker_data"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker_symbol = Column(String(10), nullable=False, index=True)  # e.g., "AAPL", "AMD"
    date = Column(Date, nullable=False)
    open_price = Column(Float)
    close_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    bid_price = Column(Float)  # Bid price from IBKR
    ask_price = Column(Float)  # Ask price from IBKR
    volume = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Composite index for efficient queries
    __table_args__ = (
        # This will be added in the database creation
    ) 