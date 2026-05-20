from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# =====================================================
# DATABASE SETUP
# =====================================================

DATABASE_URL = "sqlite:///financial_analytics.db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

# =====================================================
# USERS TABLE
# =====================================================

class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True)

    password = Column(String)

    company = Column(String)

    role = Column(String)

    location = Column(String)

    department = Column(String)

# =====================================================
# PREDICTION HISTORY TABLE
# =====================================================

class PredictionHistory(Base):

    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String)

    tenure = Column(Integer)

    monthly_charges = Column(Float)

    total_charges = Column(Float)

    probability = Column(Float)

    risk = Column(String)

    prediction_date = Column(String)

# =====================================================
# CREATE DATABASE TABLES
# =====================================================

Base.metadata.create_all(bind=engine)