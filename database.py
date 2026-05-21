from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

# =====================================================
# DATABASE CONFIGURATION
# =====================================================

DATABASE_URL = "sqlite:///financial_analytics.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

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

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        unique=True,
        nullable=False
    )

    password = Column(
        String,
        nullable=False
    )

    company = Column(String)

    role = Column(String)

    location = Column(String)

    department = Column(String)

    # USER / ADMIN
    role_type = Column(
        String,
        default="User"
    )

# =====================================================
# PREDICTION HISTORY TABLE
# =====================================================

class PredictionHistory(Base):

    __tablename__ = "prediction_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

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

# =====================================================
# SAFE DATABASE MIGRATION
# =====================================================

with engine.connect() as conn:

    try:

        conn.execute(
            text(
                """
                ALTER TABLE users
                ADD COLUMN role_type TEXT DEFAULT 'User'
                """
            )
        )

        conn.commit()

        print("✅ role_type column added successfully")

    except Exception:

        print("✅ role_type column already exists")

# =====================================================
# CREATE DEFAULT ADMIN USER
# =====================================================

db: Session = Session(bind=engine)

try:

    # CHECK IF ADMIN EXISTS
    existing_admin = db.query(User).filter(
        User.username == "admin@foa.com"
    ).first()

    if not existing_admin:

        admin_user = User(
            username="admin@foa.com",
            password="Admin@123",
            company="FOA Intelligence",
            role="Chief Administrator",
            location="Bangalore",
            department="Enterprise Security",
            role_type="Admin"
        )

        db.add(admin_user)

        db.commit()

        print("✅ Admin account created successfully")

        print("📧 Username: admin@foa.com")
        print("🔑 Password: Admin@123")

    else:

        existing_admin.role_type = "Admin"

        db.commit()

        print("✅ Existing admin upgraded successfully")

finally:

    db.close()

# =====================================================
# DATABASE SESSION FUNCTION
# =====================================================

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()

# =====================================================
# ADMIN HELPER FUNCTIONS
# =====================================================

def get_all_users():

    db = SessionLocal()

    try:

        users = db.query(User).all()

        return users

    finally:

        db.close()

# =====================================================

def delete_user(user_id):

    db = SessionLocal()

    try:

        user = db.query(User).filter(
            User.id == user_id
        ).first()

        if user:

            db.delete(user)

            db.commit()

            return True

        return False

    finally:

        db.close()

# =====================================================

def promote_to_admin(user_id):

    db = SessionLocal()

    try:

        user = db.query(User).filter(
            User.id == user_id
        ).first()

        if user:

            user.role_type = "Admin"

            db.commit()

            return True

        return False

    finally:

        db.close()

# =====================================================

def demote_to_user(user_id):

    db = SessionLocal()

    try:

        user = db.query(User).filter(
            User.id == user_id
        ).first()

        if user:

            user.role_type = "User"

            db.commit()

            return True

        return False

    finally:

        db.close()

# =====================================================

def get_total_users():

    db = SessionLocal()

    try:

        return db.query(User).count()

    finally:

        db.close()

# =====================================================

def get_total_predictions():

    db = SessionLocal()

    try:

        return db.query(PredictionHistory).count()

    finally:

        db.close()

# =====================================================

def get_high_risk_predictions():

    db = SessionLocal()

    try:

        return db.query(PredictionHistory).filter(
            PredictionHistory.risk == "HIGH RISK"
        ).count()

    finally:

        db.close()

# =====================================================

def get_admin_count():

    db = SessionLocal()

    try:

        return db.query(User).filter(
            User.role_type == "Admin"
        ).count()

    finally:

        db.close()