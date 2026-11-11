from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

app=FastAPI(title="Construction Project Intelligence Copilot", version="0.1.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "construction-copilot"}

@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    database = db.execute(text("SELECT current_database()")).scalar_one()
    pgvector_version = db.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")).scalar_one()

    return {"status": "ok", "database": database, "pgvector_version": pgvector_version}

