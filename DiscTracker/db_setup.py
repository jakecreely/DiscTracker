import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from DiscTracker.models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    print("ERROR: DATABASE_URL environment variable is not set.")
else:
    print("DATABASE_URL:", DATABASE_URL)


engine = create_engine(DATABASE_URL)

Session = sessionmaker(engine) 

def initialise_database():
    Base.metadata.create_all(engine)
    print("Database initialized successfully.")