from __future__ import annotations

import datetime
import heapq
from functools import lru_cache
from typing import TYPE_CHECKING
from typing import no_type_check

from sqlmodel import select
from sqlmodel import update

from common import config
from common import tables
from common.error import HSError
from common.session import hs_transaction
from common.typing import np_float_arr

if TYPE_CHECKING:
    from typing import AsyncIterator

    from sqlmodel import Session

    from model import GensimModel


class SecretLogic:
    def __init__(self, session: Session, dt: datetime.date | None = None):
        if dt is None:
            dt = datetime.datetime.utcnow().date()
        self.date = dt
        self.session = session

    async def get_secret(self) -> str:
        return self._get_cached_secret(session=self.session, date=self.date)

    @staticmethod
    @lru_cache
    def _get_cached_secret(session: Session, date: datetime.date) -> str:
        # TODO: this function is accessing db but is NOT ASYNC, which might be
        # problematic if we choose to do async stuff with sql in the future.
        # the reason for that is `@lru_cache` does not support async.
        query = select(tables.SecretWord)
        query = query.where(tables.SecretWord.game_date == date)

        with hs_transaction(session) as session:
            secret_word = session.exec(query).one_or_none()
            if secret_word is not None:
                return secret_word.word
            else:
                raise HSError("No secret found!", code=250722)

    async def set_secret(self, secret: str, clues: list[str]) -> None:
        with hs_transaction(self.session, expire_on_commit=False) as session:
            db_secret = tables.SecretWord(word=secret, game_date=self.date)
            session.add(db_secret)
        with hs_transaction(self.session) as session:
            for clue in clues:
                if clue:
                    session.add(tables.HotClue(secret_word_id=db_secret.id, clue=clue))

    async def get_all_secrets(
        self, with_future: bool
    ) -> list[tuple[str, str]]:  # TODO: better return type
        query = select(tables.SecretWord)
        if not with_future:
            query = query.where(tables.SecretWord.game_date < self.date)
        with hs_transaction(self.session) as session:
            secrets = session.exec(query)
            return [(secret.word, str(secret.game_date)) for secret in secrets]

    @no_type_check
    async def get_and_update_solver_count(self) -> int:
        # UPDATE RETURNING is not fully supported by sqlmodel typing yet
        query = update(tables.SecretWord)
        query = query.where(tables.SecretWord.game_date == self.date)
        query = query.values(solver_count=tables.SecretWord.solver_count + 1)
        query = query.returning(tables.SecretWord.solver_count)

        with hs_transaction(self.session) as session:
            solver_count = session.exec(query).scalar_one()
            return solver_count


class VectorLogic:
    _secret_cache: dict[str, np_float_arr] = {}

    def __init__(self, session: Session, model: GensimModel, dt: datetime.date):
        self.model = model
        self.session = session
        self.date = str(dt)
        self.secret_logic = SecretLogic(self.session, dt=dt)

    async def get_vector(self, word: str) -> np_float_arr | None:
        return await self.model.get_vector(word)

    async def get_similarities(self, words: list[str]) -> np_float_arr:
        secret_vector = await self.get_secret_vector()
        return await self.model.get_similarities(words, secret_vector)

    async def get_secret_vector(self) -> np_float_arr:
        if self._secret_cache.get(self.date) is None:
            secret = await self.secret_logic.get_secret()
            vector = await self.get_vector(secret)
            if vector is None:
                raise ValueError("No secret found!")  # TODO: better exception
            self._secret_cache[self.date] = vector
        return self._secret_cache[self.date]

    async def get_similarity(self, word: str) -> float:
        word_vector = await self.get_vector(word)
        if word_vector is None:
            raise HSError("Word not found", code=100796)
        secret_vector = await self.get_secret_vector()
        return await self.calc_similarity(secret_vector, word_vector)

    async def calc_similarity(self, vec1: np_float_arr, vec2: np_float_arr) -> float:
        return await self.model.calc_similarity(vec1, vec2)

    async def get_and_update_solver_count(self) -> int:
        solver_count: int = await self.secret_logic.get_and_update_solver_count()
        return solver_count

    def iterate_all(self) -> AsyncIterator[tuple[str, np_float_arr]]:
        return self.model.iterate_all()


class CacheSecretLogic:
    _secret_cache_key_fmt = "hs:{}:{}"
    _cache_dict: dict[str, list[str]] = {}
    MAX_CACHE = 50

    def __init__(
        self,
        session: Session,
        secret: str,
        dt: datetime.date,
        model: GensimModel,
    ):
        self.session = session
        if dt is None:
            dt = datetime.datetime.utcnow().date()
        self.date_ = dt
        self.date = str(dt)
        self.vector_logic = VectorLogic(self.session, model=model, dt=dt)
        self.secret = secret
        self._secret_cache_key: str | None = None
        self.model = model.model
        self.words = self.model.key_to_index.keys()
        self.session = session

    def _iterate_all_wv(self) -> AsyncIterator[tuple[str, np_float_arr]]:
        return self.vector_logic.iterate_all()

    async def simulate_set_secret(self, force: bool = False) -> None:
        """Simulates setting a secret, but does not actually do it.
        In order to actually set the secret, call do_populate()
        """
        if not force:
            try:
                await self.vector_logic.secret_logic.get_secret()
                raise ValueError("There is already a secret for this date")
            except HSError:
                pass

            query = select(tables.SecretWord.game_date)  # type: ignore
            query = query.where(tables.SecretWord.word == self.secret)
            with hs_transaction(self.session) as session:
                date = session.exec(query).one_or_none()
            if date is not None:
                raise ValueError(f"This word was a secret on {date}")
            if self.secret not in self.words:
                raise ValueError("This word is not in the model")

        secret_vec = self.model[self.secret]

        nearest: list[tuple[float, str]] = []
        async for word, vec in self._iterate_all_wv():
            s = await self.vector_logic.calc_similarity(vec, secret_vec)
            heapq.heappush(nearest, (s, word))
            if len(nearest) > 1000:
                heapq.heappop(nearest)
        nearest.sort()
        self._cache_dict[self.date] = [w[1] for w in nearest]

    async def do_populate(self, clues: list[str]) -> None:
        # expiration = (  # TODO: implement this for SQL
        #     self.date_
        #     - datetime.datetime.now(datetime.UTC).date()
        #     + datetime.timedelta(days=4)
        # )
        await self.vector_logic.secret_logic.set_secret(self.secret, clues)
        closest1000 = []
        for out_of, word in enumerate(self._cache_dict[self.date], start=1):
            closest1000.append(tables.Closest1000(word=word, out_of_1000=out_of))
        with hs_transaction(self.session) as session:
            secret_word = select(tables.SecretWord).where(
                tables.SecretWord.game_date == self.date,
                tables.SecretWord.word == self.secret,
            )
            secret_word = session.execute(secret_word).scalar_one()
            secret_word.closest1000 = closest1000  # type: ignore
            session.add(secret_word)

    async def get_cache(self) -> list[str]:
        cache = self._cache_dict.get(self.date)
        if cache is None or len(cache) < 1000:
            if len(self._cache_dict) > self.MAX_CACHE:
                self._cache_dict.clear()
            with hs_transaction(self.session) as session:
                query = select(tables.SecretWord).where(
                    tables.SecretWord.game_date == self.date,
                    tables.SecretWord.word == self.secret,
                )
                secret_word = session.exec(query).one()
                if secret_word is None:
                    raise HSError("Secret not found", code=100796)
                cached = [
                    closest.word
                    for closest in sorted(
                        secret_word.closest1000, key=lambda c: c.out_of_1000
                    )
                ]
            self._cache_dict[self.date] = cached
        return self._cache_dict[self.date]

    async def get_cache_score(self, word: str) -> int:
        try:
            return (await self.get_cache()).index(word) + 1
        except ValueError:
            return -1


class EasterEggLogic:
    EASTER_EGGS: dict[str, str] = config.easter_eggs

    @staticmethod
    def get_easter_egg(phrase: str) -> str | None:
        return EasterEggLogic.EASTER_EGGS.get(phrase)
