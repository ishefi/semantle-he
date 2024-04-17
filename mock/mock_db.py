from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from sqlalchemy import Engine
from sqlalchemy import event
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import StaticPool
from sqlmodel import create_engine

if TYPE_CHECKING:
    from typing import Any
    from typing import TypeVar

    T = TypeVar("T", bound=SQLModel)


def collation(string1: str, string2: str) -> int:
    if string1 == string2:
        return 0
    elif string1 > string2:
        return 1
    else:
        return -1


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(
    dbapi_connection: sqlite3.Connection, dummy_connection_record: Any
) -> None:
    dbapi_connection.create_collation("Hebrew_100_CI_AI_SC_UTF8", collation)
    dbapi_connection.create_collation("Hebrew_CI_AI", collation)
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class MockDb:
    def __init__(self) -> None:
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
        SQLModel.metadata.create_all(self.engine)

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
