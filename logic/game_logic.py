from __future__ import annotations

import datetime
import heapq
from typing import TYPE_CHECKING
from typing import no_type_check

from sqlmodel import select
from sqlmodel import update

from common import config
from common import tables
from common.session import hs_transaction
from common.typing import np_float_arr

if TYPE_CHECKING:
    from typing import Any
    from typing import AsyncIterator
    from typing import Generator

    from redis.asyncio import Redis
    from sqlmodel import Session

    from model import GensimModel


class SecretLogic:
    def __init__(self, session: Session, dt: datetime.date | None = None):
        if dt is None:
            dt = datetime.datetime.utcnow().date()
        self.date = dt
        self.session = session

    async def get_secret(self) -> str | None:
        query = select(tables.SecretWord)
        query = query.where(tables.SecretWord.game_date == self.date)

        with hs_transaction(self.session) as session:
            secret_word = session.exec(query).one_or_none()
            if secret_word is not None:
                return secret_word.word
            else:
                return None

    async def set_secret(self, secret: str) -> None:
        with hs_transaction(self.session) as session:
            session.add(tables.SecretWord(word=secret, game_date=self.date))

    async def get_all_secrets(
        self, with_future: bool
    ) -> Generator[tuple[str, str], None, None]:  # TODO: better return type
        query = select(tables.SecretWord)
        if not with_future:
            query = query.where(tables.SecretWord.game_date < self.date)
        with hs_transaction(self.session) as session:
            secrets = session.exec(query)
            return ((secret.word, str(secret.game_date)) for secret in secrets)

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
            if secret is None:
                raise ValueError("No secret found!")  # TODO: better exception
            vector = await self.get_vector(secret)
            if vector is None:
                raise ValueError("No secret found!")  # TODO: better exception
            self._secret_cache[self.date] = vector
        return self._secret_cache[self.date]

    async def get_similarity(self, word: str) -> float | None:
        word_vector = await self.get_vector(word)
        if word_vector is None:
            return None
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
        redis: Redis[Any],
        secret: str,
        dt: datetime.date,
        model: GensimModel,
    ):
        self.session = session
        self.redis = redis
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

    @property
    def secret_cache_key(self) -> str:
        if self._secret_cache_key is None:
            self._secret_cache_key = self._secret_cache_key_fmt.format(
                self.secret, self.date
            )
        return self._secret_cache_key

    def _get_secret_vector(self) -> np_float_arr:
        vector: np_float_arr = self.model[self.secret]
        return vector

    def _iterate_all_wv(self) -> AsyncIterator[tuple[str, np_float_arr]]:
        return self.vector_logic.iterate_all()

    async def set_secret(self, dry: bool = False, force: bool = False) -> None:
        if not force:
            if await self.vector_logic.secret_logic.get_secret() is not None:
                raise ValueError("There is already a secret for this date")

            query = select(tables.SecretWord.game_date)  # type: ignore
            query = query.where(tables.SecretWord.word == self.secret)
            with hs_transaction(self.session) as session:
                date = session.exec(query).one_or_none()
            if date is not None:
                raise ValueError(f"This word was a secret on {date}")
            if self.secret not in self.words:
                raise ValueError("This word is not in the model")

        secret_vec = self._get_secret_vector()

        nearest: list[tuple[float, str]] = []
        async for word, vec in self._iterate_all_wv():
            s = await self.vector_logic.calc_similarity(vec, secret_vec)
            heapq.heappush(nearest, (s, word))
            if len(nearest) > 1000:
                heapq.heappop(nearest)
        nearest.sort()
        self._cache_dict[self.date] = [w[1] for w in nearest]
        if not dry:
            await self.do_populate()

    async def do_populate(self) -> None:
        expiration = (
            self.date_ - datetime.datetime.utcnow().date() + datetime.timedelta(days=4)
        )
        await self.redis.delete(self.secret_cache_key)
        await self.redis.rpush(self.secret_cache_key, *await self.cache)
        await self.redis.expire(self.secret_cache_key, expiration)
        await self.vector_logic.secret_logic.set_secret(self.secret)

    @property
    async def cache(self) -> list[str]:
        cache = self._cache_dict.get(self.date)
        if cache is None or len(cache) < 1000:
            if len(self._cache_dict) > self.MAX_CACHE:
                self._cache_dict.clear()
            cached: list[str] = await self.redis.lrange(self.secret_cache_key, 0, -1)
            self._cache_dict[self.date] = cached
        return self._cache_dict[self.date]

    async def get_cache_score(self, word: str) -> int:
        try:
            return (await self.cache).index(word) + 1
        except ValueError:
            return -1


class EasterEggLogic:
    EASTER_EGGS: dict[str, str] = config.easter_eggs

    @staticmethod
    def get_easter_egg(phrase: str) -> str | None:
        return EasterEggLogic.EASTER_EGGS.get(phrase)
