import logging

from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.configuration import Configuration
from app.database.migrations import router


class DatabaseConnection:
    def __init__(self, configuration: Configuration):
        self.engine = create_engine(configuration.database_url)
        self.make_session = sessionmaker(bind=self.engine)
        self.run_migrations()

    def run_migrations(self):
        logging.info('Running pending migrations')
        router.run_migrations(self.engine)
