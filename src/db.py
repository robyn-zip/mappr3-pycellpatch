from dotenv import load_dotenv
import logging
from os import environ
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from models import Base


class CellDatabase:

    def __init__(self, **kwargs):
        self._url = URL(
            kwargs.get('driver'),
            kwargs.get('username'),
            kwargs.get('password'),
            kwargs.get('hostname'),
            kwargs.get('port'),
            kwargs.get('database', 'mappr3_cells'),
            kwargs.get('query', {})
        )

        try:
            self._url.query['sslmode'] = 'require'
            self._engine = create_engine(self._url, echo=False)
            self._engine.connect().close()
        except OperationalError:
            try:
                logging.warning('Database connection failure, trying without SSL')
                self._url.query['sslmode'] = 'prefer'
                self._engine = create_engine(self._url, echo=False)
            except OperationalError as err:
                logging.error('Failed to connect to database: %s', err.code)

        self._session = sessionmaker(bind=self._engine)
        self._db = self._session()

        # Create the schema on the database. It won't replace any existing schema
        Base.metadata.create_all(self._engine)
        logging.info('Database object initialised')

    def get_session(self) -> Session:
        return self._db

    def commit(self) -> None:
        logging.info('Committed database changes')
        self._db.commit()


if __name__ == '__main__':
    load_dotenv()

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(levelname)s - %(message)s')

    db = CellDatabase(
        driver='postgresql+psycopg',
        username=environ['CELLS_DB_USERNAME'],
        password=environ['CELLS_DB_PASSWORD'],
        hostname=environ['CELLS_DB_HOSTNAME'],
        port=5432,
        database='mappr3_cells',
        query={
            'client_encoding': 'utf8'
        }
    )

    db.commit()
