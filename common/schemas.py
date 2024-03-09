#!/usr/bin/env python
import datetime

from pydantic import BaseModel
from pydantic import validator


class DistanceResponse(BaseModel):
    guess: str
    similarity: float | None
    distance: int
    egg: str | None = None
    solver_count: int | None = None
    guess_number: int = 0


class UserStatistics(BaseModel):
    game_streak: int
    highest_rank: int | None
    total_games_played: int
    total_games_won: int
    average_guesses: float

    @validator("average_guesses")  # TODO: use some other parsing method
    def result_check(cls, v: float) -> float:
        ...
        return round(v, 2)


class Subscription(BaseModel):
    verification_token: str
    message_id: str
    timestamp: datetime.datetime
    email: str
    amount: int
    tier_name: str | None = None
