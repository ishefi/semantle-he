import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field
from sqlmodel import SQLModel


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: str = Field(unique=True)
    user_type: str = "User"  # TODO: enum
    active: bool = True
    picture: str
    given_name: str
    family_name: str
    first_login: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    subscription_expiry: datetime.datetime | None = None


class UserHistory(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "game_date", "guess"),)

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    guess: str
    similarity: float | None
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
    word: str = Field(unique=True)
    game_date: datetime.date
    solver_count: int = 0


class UserSubscription(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    amount: float
    tier_name: str | None
    uuid: str = Field(unique=True)
    timestamp: datetime.datetime
