from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from halide_api.config import settings
from sqlalchemy.orm import Session

class Base(DeclarativeBase):
    pass

engine = create_engine(settings.database_url_pooled, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    with SessionLocal() as session:
        yield session
        
SessionDep = Annotated[Session, Depends(get_db)]