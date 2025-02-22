from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db, fetch_hello_world, insert_hello_world

# Initialize FastAPI app
app = FastAPI()

# Ensure the database has an entry
insert_hello_world()

# API Endpoint - Fetch "Hello, World!" from DB
@app.get("/hello-world")
def get_hello_world(db: Session = Depends(get_db)):
    result = fetch_hello_world(db)
    if result:
        return {"message": result.message}
    else:
        return {"message": "No data found"}