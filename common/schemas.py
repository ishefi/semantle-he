#!/usr/bin/env python
from typing import Optional
from pydantic import BaseModel
from pydantic import validator


class DistanceResponse(BaseModel):
    guess: str
    similarity: Optional[float]
    distance: int
    egg: Optional[str] = None
    solver_count: Optional[int] = None
    guess_number: int = 0


class UserStatistics(BaseModel):
    game_streak: int
    highest_rank: Optional[int]
    total_games_played: int
    total_games_won: int
    average_guesses: float

    @validator('average_guesses')
    def result_check(cls, v):
        ...
        return round(v, 2)