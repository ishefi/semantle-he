#!/usr/bin/env python
from typing import Optional
from pydantic import BaseModel


class DistanceResponse(BaseModel):
    guess: str
    similarity: Optional[float]
    distance: int
    egg: Optional[str] = None
    solver_count: Optional[int] = None
    guess_number: int = 0
