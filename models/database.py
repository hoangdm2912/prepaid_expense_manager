"""Database models using SQLAlchemy."""
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from config.settings import settings

Base = declarative_base()


class Expense(Base):
    """Main expense record."""
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(10), nullable=False, index=True)  # 242xxx format
    name = Column(String(255), nullable=False)
    document_code = Column(String(50), nullable=True)  # Document/voucher code for identification
    total_amount = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)  # End date for allocation
    sub_code = Column(String(10), nullable=False)  # 9995 or 9996
    allocation_months = Column(Integer, nullable=True)  # Calculated from dates, kept for compatibility
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    allocations = relationship("Allocation", back_populates="expense", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="expense", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="expense", cascade="all, delete-orphan")


class Allocation(Base):
    """Quarterly allocation record."""
    __tablename__ = "allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    quarter = Column(Integer, nullable=False)  # 1, 2, 3, 4
    year = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    days_in_quarter = Column(Integer, nullable=False)  # Actual days in this quarter
    start_date = Column(Date, nullable=False)  # Quarter start date (or expense start if later)
    end_date = Column(Date, nullable=False)  # Quarter end date (or expense end if earlier)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    expense = relationship("Expense", back_populates="allocations")


class Document(Base):
    """Uploaded document reference."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    drive_url = Column(Text, nullable=True)  # Google Drive shareable link
    drive_file_id = Column(String(255), nullable=True)  # Google Drive file ID
    uploaded_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    expense = relationship("Expense", back_populates="documents")


class Notification(Base):
    """Notification log."""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    notification_type = Column(String(50), nullable=False)  # 'email' or 'zalo'
    status = Column(String(50), nullable=False)  # 'sent', 'failed', 'pending'
    message = Column(Text, nullable=True)
    sent_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    expense = relationship("Expense", back_populates="notifications")


# Ensure database directory exists for SQLite
if "sqlite" in settings.database_url:
    try:
        # Extract path from URL (e.g. sqlite:///./data/expenses.db -> ./data/expenses.db)
        db_path = settings.database_url.replace("sqlite:///", "")
        abs_db_path = os.path.abspath(db_path)
        db_dir = os.path.dirname(abs_db_path)
        
        print(f"DATABASE DIAGNOSTICS:")
        print(f"  - Target DB Path: {abs_db_path}")
        print(f"  - Target Directory: {db_dir}")
        
        # Create directory if it doesn't exist
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"  - Created directory: {db_dir}")
            
        # Aggressively try to ensure directory is writable
        if os.path.exists(db_dir):
            try:
                os.chmod(db_dir, 0o777)
                print(f"  - Set directory permissions to 777: {db_dir}")
            except Exception as e:
                print(f"  - Warning: Could not chmod directory: {e}")

        # Check permissions if file exists
        if os.path.exists(abs_db_path):
            is_writable = os.access(abs_db_path, os.W_OK)
            print(f"  - File exists: Yes (Writable: {is_writable})")
            if not is_writable:
                try:
                    os.chmod(abs_db_path, 0o666)
                    print(f"  - Fixed file permissions (666): {abs_db_path}")
                except Exception as e:
                    print(f"  - Warning: Could not chmod file: {e}")
        else:
            print(f"  - File exists: No (will be created by create_all)")
            
    except Exception as e:
        print(f"DATABASE DIAGNOSTICS ERROR: {e}")

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
