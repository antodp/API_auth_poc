from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Database URL (SQLite for local testing, but can be swapped for PostgreSQL, MySQL, etc.)
DATABASE_URL = "sqlite:///./hello_world_db.sqlite"

# Create database engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define HelloWorld Table
class HelloWorld(Base):
    __tablename__ = "hello_world"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String)

# Create tables in the database
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to fetch Hello World message
def fetch_hello_world(db: Session):
    return db.query(HelloWorld).first()

# Function to insert Hello World message (used to populate DB)
def insert_hello_world():
    db = SessionLocal()
    if not db.query(HelloWorld).first():
        new_message = HelloWorld(message="Hello, World!")
        db.add(new_message)
        db.commit()
    db.close()