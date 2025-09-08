from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./radar.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=True)  # Optional for simple email auth
    plan = Column(String, default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    searches = relationship("Search", back_populates="user")
    automations = relationship("Automation", back_populates="user")

class Search(Base):
    __tablename__ = "searches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query = Column(Text, nullable=False)
    filters = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="searches")
    results = relationship("Result", back_populates="search")
    columns = relationship("CustomColumn", back_populates="search")
    automations = relationship("Automation", back_populates="search")

class Result(Base):
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("searches.id"), nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    snippet = Column(Text, nullable=True)
    country = Column(String, nullable=True)
    language = Column(String, nullable=True)
    date = Column(String, nullable=True)
    category = Column(String, nullable=True)
    status = Column(String, nullable=True)
    source = Column(String, nullable=True)
    score = Column(Integer, default=0)
    result_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    search = relationship("Search", back_populates="results")
    column_values = relationship("ColumnValue", back_populates="result")

class CustomColumn(Base):
    __tablename__ = "columns"
    
    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("searches.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    generated_by_ai = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    search = relationship("Search", back_populates="columns")
    column_values = relationship("ColumnValue", back_populates="column")

class ColumnValue(Base):
    __tablename__ = "column_values"
    
    id = Column(Integer, primary_key=True, index=True)
    column_id = Column(Integer, ForeignKey("columns.id"), nullable=False)
    result_id = Column(Integer, ForeignKey("results.id"), nullable=False)
    value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    column = relationship("CustomColumn", back_populates="column_values")
    result = relationship("Result", back_populates="column_values")

class Automation(Base):
    __tablename__ = "automations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    search_id = Column(Integer, ForeignKey("searches.id"), nullable=False)
    frequency = Column(String, nullable=False)  # "24h", "weekly", "monthly"
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="automations")
    search = relationship("Search", back_populates="automations")

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
