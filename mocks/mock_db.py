from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from common.tables import *


class MockDb(object):
    def __init__(self):
        self.db_uri = "sqlite:///:memory:"
        self.engine = create_engine(self.db_uri)
        self.session_factory = scoped_session(
            sessionmaker(
                bind=self.engine,
                autocommit=True,
                expire_on_commit=False,
                autoflush=True,
            )
        )
        BaseModel.metadata.create_all(self.engine)

    def add(self, entity):
        session = self.session_factory()
        session.begin()
        session.add(entity)
        session.commit()
        session.refresh(entity)
        return entity
