"""
SQLAlchemy models for TapApply.
Supports SQLite (dev) and PostgreSQL (prod) — detected from DATABASE_URL prefix.
"""

from sqlalchemy import (
    create_engine, Column, String, Integer, Text, DateTime, Boolean,
    Float, Enum as SQLEnum, ForeignKey, JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from enum import Enum


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tapapply.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class CountryEnum(str, Enum):
    UK = "UK"
    USA = "USA"
    CANADA = "CANADA"
    AUSTRALIA = "AUSTRALIA"
    NEW_ZEALAND = "NEW_ZEALAND"
    GERMANY = "GERMANY"
    FRANCE = "FRANCE"
    NETHERLANDS = "NETHERLANDS"
    IRELAND = "IRELAND"
    SPAIN = "SPAIN"


class SectorEnum(str, Enum):
    TECH_SOFTWARE = "Tech & Software"
    FINANCE_BANKING = "Finance & Banking"
    HEALTHCARE_MEDICAL = "Healthcare & Medical"
    MARKETING_CREATIVE = "Marketing & Creative"
    ENGINEERING_OPERATIONS = "Engineering & Operations"


class ApplicationStatusEnum(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    OFFER_EXTENDED = "offer_extended"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profiles = relationship("Profile", back_populates="user")
    manual_profiles = relationship("ManualProfile", back_populates="user")
    applications = relationship("JobApplication", back_populates="user")
    jobs = relationship("Job", back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    country = Column(SQLEnum(CountryEnum), index=True)
    sector = Column(SQLEnum(SectorEnum), index=True)
    cv_text = Column(Text)
    cv_original_filename = Column(String)
    linkedin_url = Column(String)
    github_url = Column(String)
    website_url = Column(String)
    tone_preference = Column(String, default="professional")
    onboarding_path = Column(String, default="cv")  # "cv" or "manual"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profiles")


class ManualProfile(Base):
    """Stores structured profile data entered through the manual intake form (Path B)."""
    __tablename__ = "manual_profiles"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    full_name = Column(String)
    email = Column(String)
    phone = Column(String)
    location = Column(String)
    linkedin_url = Column(String)
    github_url = Column(String)
    professional_summary = Column(Text)
    experience_entries = Column(JSON)   # List[{title, company, location, start, end, bullets}]
    education_entries = Column(JSON)    # List[{degree, institution, year, honours}]
    skills_technical = Column(JSON)     # List[str]
    skills_soft = Column(JSON)          # List[str]
    certifications = Column(JSON)       # List[str]
    target_role = Column(String)
    target_level = Column(String, default="mid")   # junior | mid | senior | executive
    generated_cv_text = Column(Text)    # ATS-optimized CV produced by ats_builder
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="manual_profiles")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    title = Column(String, index=True)
    company = Column(String, index=True)
    location = Column(String)
    country = Column(SQLEnum(CountryEnum), index=True)
    sector = Column(SQLEnum(SectorEnum), index=True)
    salary_min = Column(Float)
    salary_max = Column(Float)
    currency = Column(String, default="USD")
    job_description = Column(Text)
    job_url = Column(String, unique=True, index=True)
    source = Column(String)
    posted_date = Column(DateTime)
    closing_date = Column(DateTime)
    discovered_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="jobs")
    applications = relationship("JobApplication", back_populates="job")


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    job_id = Column(String, ForeignKey("jobs.id"), index=True)
    status = Column(SQLEnum(ApplicationStatusEnum), default=ApplicationStatusEnum.PENDING, index=True)
    cover_letter = Column(Text)
    answers = Column(JSON)
    submitted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    interview_sessions = relationship("InterviewSession", back_populates="application")


class InterviewSession(Base):
    """Generated interview prep materials for a specific application."""
    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True, index=True)
    application_id = Column(String, ForeignKey("job_applications.id"), index=True)
    user_id = Column(String, ForeignKey("users.id"), index=True)
    company_brief = Column(Text)
    key_challenges = Column(JSON)   # List[str]
    culture_signals = Column(JSON)  # List[str]
    mock_questions = Column(JSON)   # List[{question, guidance, star_template}]
    generated_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("JobApplication", back_populates="interview_sessions")


class AutopilotState(Base):
    __tablename__ = "autopilot_state"

    id = Column(String, primary_key=True, default="singleton")
    is_enabled = Column(Boolean, default=False, index=True)
    jobs_analyzed = Column(Integer, default=0)
    applications_placed = Column(Integer, default=0)
    actions_required = Column(Integer, default=0)
    current_job_id = Column(String)
    last_activity = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
