from database import engine
from models import Base

# Функция для создания таблиц в базе данных
def create_tables(engine):
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    create_tables(engine)