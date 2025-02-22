from sqlalchemy.orm import Session
from database import SessionLocal, HelloWorld

# Create a database session
db = SessionLocal()

# Check if data exists
existing_entry = db.query(HelloWorld).first()

# Insert message if not exists
if not existing_entry:
    new_message = HelloWorld(message="Hello, World!")
    db.add(new_message)
    db.commit()

db.close()