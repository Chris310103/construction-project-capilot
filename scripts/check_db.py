from sqlalchemy import text

from app.db.session import engine

def main():
    with engine.connect() as connection:
        database=connection.execute(text("SELECT current_database()")).scalar_one()
        pgvector_version = connection.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")).scalar_one()

    print(f"Connected to database: {database}")
    print(f"pgvector version: {pgvector_version}")


if __name__ == "__main__":
    main()
