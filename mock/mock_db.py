from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import event
from sqlalchemy import Engine
from sqlmodel import StaticPool
from sqlmodel import create_engine
from sqlmodel import Session

from common import tables


if TYPE_CHECKING:
    from typing import TypeVar
    T = TypeVar("T", bound=tables.SQLModel)


def collation(string1, string2):
    if string1 == string2:
        return 0
    elif string1 > string2:
        return 1
    else:
        return -1

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, dummy_connection_record):
    dbapi_connection.create_collation("Hebrew_100_CI_AI_SC_UTF8", collation)
    dbapi_connection.create_collation("Hebrew_CI_AI", collation)
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class MockDb:
    def __init__(self):
        self.db_uri = "sqlite:///:memory:?cache=shared"
        self.engine = create_engine(
            self.db_uri,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.session = Session(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=True,
        )
        tables.SQLModel.metadata.create_all(self.engine)

    def add(self, entity: T) -> T:
        self.session.begin()
        self.session.add(entity)
        self.session.commit()
        return entity

    def add_many(self, entities: list[T]) -> None:
        self.session.begin()
        for entity in entities:
            self.session.add(entity)
        self.session.commit()
        for entity in entities:
            self.session.refresh(entity)
