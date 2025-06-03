import datetime

from sqlalchemy import Index
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: str = Field(String(128), unique=True)
    user_type: str = "User"  # TODO: enum
    active: bool = True
    picture: str
    given_name: str
    family_name: str
    first_login: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    # subscription_expiry: datetime.datetime | None = None
    subscriptions: "UserSubscription" = Relationship()


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
    guess: str = Field(String(32))
    similarity: float
    distance: int
    egg: str | None = None
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
    word: str = Field(String(32), unique=True)
    game_date: datetime.date
    solver_count: int = 0


class UserSubscription(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    amount: float
    tier_name: str | None
    uuid: str = Field(String(36), unique=True)
    timestamp: datetime.datetime


class HotClue(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("secret_word_id", "clue"),)

    id: int = Field(default=None, primary_key=True)
    secret_word_id: int = Field(foreign_key="secretword.id", index=True)
    clue: str = Field(String(32))

    secret: SecretWord = Relationship()
