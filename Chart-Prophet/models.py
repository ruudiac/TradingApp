import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get('DATABASE_URL')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    symbol = Column(String(20), nullable=True)
    recommendation = Column(String(20), nullable=False)
    confidence_level = Column(String(20), nullable=True)
    trend_direction = Column(String(20), nullable=True)
    outcome = Column(String(20), nullable=True)
    profit_loss = Column(Float, nullable=True)
    indicator_type = Column(String(50), nullable=True)
    rsi_signal = Column(String(20), nullable=True)
    macd_signal = Column(String(20), nullable=True)
    entry_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    raw_analysis = Column(Text, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
