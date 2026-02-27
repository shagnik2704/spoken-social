# ============================================================
# Database Connection — Engine + Session
# ============================================================
# Engine = the connection to PostgreSQL
# SessionLocal = a factory that creates DB sessions
# Base = all models inherit from this
# ============================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Connection string format: postgresql://user@host/dbname
# Postgres.app on Mac doesn't need a password for local connections
DATABASE_URL = "postgresql://shagniksarkar@localhost/spoken_social"

engine = create_engine(DATABASE_URL, echo=False)
# echo=True would print every SQL query (useful for debugging)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """All models inherit from this. It tracks all your tables."""
    pass


def get_db():
    """
    FastAPI dependency that gives each request its own DB session.
    
    Usage in routes:
        @router.get('/me')
        def get_me(db: Session = Depends(get_db)):
            user = db.query(User).filter_by(id=...).first()
    
    The 'finally' block ensures the session is always closed,
    even if the route throws an error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
