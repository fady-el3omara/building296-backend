from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use the schema/building296.db path (relative to root)
DATABASE_URL = "sqlite:///schema/building296.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
