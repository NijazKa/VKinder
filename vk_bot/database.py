import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

engine = sq.create_engine(DATABASE_URL, connect_args={'client_encoding': 'utf8'})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    return SessionLocal()