from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# docker run --name db-postgres -p 5432:5432 -e POSTGRES_USER=eles -e POSTGRES_PASSWORD=567234 -e POSTGRES_DB=fastapi_db -d postgres
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://eles:567234@localhost:5432/fastapi_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    description = Column(String(250))
    done = Column(Boolean, default=False)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    lastname = Column(String(50))
    email = Column(String(50))
    phone = Column(String(50))
    born_date = Date()
    description = Column(String(250))


Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
