import datetime
from typing import Any

from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel


def HebrewString(length: int | None = None, *args: Any, **kwargs: Any) -> Any:
    return Field(
        sa_type=String(length, collation="Hebrew_100_CI_AI_SC_UTF8"), *args, **kwargs
    )  # type: ignore


def NoFinalHebrewString(length: int | None = None, *args: Any, **kwargs: Any) -> Any:
    """Hebrew string with no different indexing for fin:20al and non-final chars"""
    return Field(sa_type=String(length, collation="Hebrew_CI_AI"), *args, **kwargs)  # type: ignore


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: str = NoFinalHebrewString(128, unique=True)
    user_type: str = "User"  # TODO: enum
    active: bool = True
    picture: str
    given_name: str = NoFinalHebrewString()
    family_name: str = NoFinalHebrewString()
    first_login: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    subscription_expiry: datetime.datetime | None = None


class UserHistory(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "game_date", "guess"),
        Index(
            "nci_user_id__game_date",
            "user_id",
            "game_date",
            mssql_include=["distance", "egg", "guess", "similarity", "solver_count"],
        ),
    )

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    guess: str = HebrewString(32)
    similarity: float
    distance: int
    egg: str | None = NoFinalHebrewString(default=None)
    game_date: datetime.date
    solver_count: int | None = None


class UserClueCount(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "game_date"),)

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    clue_count: int
    game_date: datetime.date


class SecretWord(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("game_date"), UniqueConstraint("word"))

    id: int = Field(default=None, primary_key=True)
    word: str = HebrewString(32, unique=True)
    game_date: datetime.date
    solver_count: int = 0


class UserSubscription(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    amount: float
    tier_name: str | None
    uuid: str = NoFinalHebrewString(36, unique=True)
    timestamp: datetime.datetime


class HotClue(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("secret_word_id", "clue"),)

    id: int = Field(default=None, primary_key=True)
    secret_word_id: int = Field(foreign_key="secretword.id", index=True)
    clue: str = HebrewString(32)

    secret: SecretWord = Relationship()
