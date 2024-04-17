import datetime
import unittest

import pytest
from sqlmodel import Session

from common import tables
from common.error import HSError
from logic.game_logic import SecretLogic
from mock.mock_db import MockDb


class TestGameLogic(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.db = MockDb()
        self.date = datetime.date(2021, 1, 1)
        self.testee = SecretLogic(session=self.db.session, dt=self.date)

    async def test_no_secret(self) -> None:
        # act & assert
        with pytest.raises(HSError):
            await self.testee.get_secret()

    async def test_get_secret(self) -> None:
        # arrange
        db_secret = tables.SecretWord(word="test", game_date=self.date)
        self.db.add(db_secret)

        # act
        secret = await self.testee.get_secret()

        # assert
        self.assertEqual(db_secret.word, secret)

    async def test_get_secret__cache(self) -> None:
        # arrange
        cached = self.db.add(tables.SecretWord(word="cached", game_date=self.date))
        await self.testee.get_secret()
        with Session(self.db.engine) as session:
            db_secret = session.get(tables.SecretWord, cached.id)
            assert db_secret is not None
            db_secret.word = "not_cached"
            session.add(db_secret)
            session.commit()

        # act
        secret = await self.testee.get_secret()

        # assert
        self.assertEqual("cached", secret)

    async def test_get_secret__dont_cache_if_no_secret(self) -> None:
        # arrange
        try:
            await self.testee.get_secret()
        except HSError:
            pass
        self.db.add(tables.SecretWord(word="not_cached", game_date=self.date))

        # act
        secret = await self.testee.get_secret()

        # assert
        self.assertEqual("not_cached", secret)
