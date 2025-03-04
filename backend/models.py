# backend/models.py

from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Define the base class for declarative models
Base = declarative_base()

class PolicyAnalysis(Base):
    """
    Database model for storing policy analysis results.
    """
    __tablename__ = 'policy_analysis'
    
    id = Column(Integer, primary_key=True)
    domain = Column(String, unique=True)
    title = Column(Text)
    url = Column(Text)
    status = Column(String, default='not_processed')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    summary = Column(Text)
    key_points = Column(Text)
    concerns = Column(Text)
    llm_model = Column(String)

    def __repr__(self):
        return f"<PolicyAnalysis(domain='{self.domain}')>"

# Initialize the database engine (SQLite)
engine = create_engine('sqlite:///database.db', echo=True)

# Create all tables in the database
Base.metadata.create_all(engine)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)