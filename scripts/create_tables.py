from app.db import models
from app.db.base import Base
from app.db.session import engine

def main():
    Base.metadata.create_all(bind=engine)
    print("Registered tables:", list(Base.metadata.tables.keys()))

if __name__=="__main__":
    main()