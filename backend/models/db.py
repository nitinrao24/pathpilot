import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL","sqlite:///./pathpilot.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RouteQuery(Base):
    __tablename__ = "route_queries"
    id              = Column(Integer, primary_key=True, index=True)
    source_id       = Column(String)
    source_name     = Column(String)
    target_id       = Column(String)
    target_name     = Column(String)
    distance_m      = Column(Integer)
    walk_min        = Column(Integer)
    hops            = Column(Integer)
    congestion_used = Column(Boolean, default=False)
    hour            = Column(Float)
    dow             = Column(Integer)
    queried_at      = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
