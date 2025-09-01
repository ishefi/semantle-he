# type: ignore
import datetime
from typing import Any

import tqdm  # type: ignore
from sqlalchemy import func
from sqlmodel import Session
from sqlmodel import create_engine
from sqlmodel import select

from common import tables
from common.session import hs_transaction

origin_db = "mssql+pyodbc://semantle:8$#&MdSX[wYXxq'<@semantledb.database.windows.net:1433/SemantleDB?driver=ODBC+Driver+18+for+SQL+Server&encrypt=yes&trustServerCertificate=no&connectionTimeout=30"
dest_db = "postgresql://semantle_user:w5HvpnpIDvfJWOZeXeSeL90MMuzuZ4rO@dpg-d0s2bs2dbo4c73bae3sg-a.frankfurt-postgres.render.com/semantle"


def get_session(db_url: str) -> Session:
    engine = create_engine(db_url)
    return Session(engine)


origin_session = get_session(origin_db)


def get_things_to_update() -> tuple[Any]:
    dest_session = get_session(dest_db)
    user_query = select(
        tables.User
    )  # .where(tables.User.first_login > datetime.datetime(2025, 5, 28))
    clue_count_query = select(
        tables.UserClueCount
    )  # .where(tables.UserClueCount.game_date > datetime.datetime(2025, 5, 28))
    secret_query = select(tables.SecretWord)
    subscription_query = select(tables.UserSubscription)
    hclue_query = select(tables.HotClue)

    history_query = select(tables.UserHistory)
    history_query = history_query.where(tables.UserHistory.id >= 22000000)
    # history_query = history_query.where(tables.UserHistory.id <= 19000000)

    count_user_query = select(func.count(tables.User.id))  # type: ignore
    count_clue_count_query = select(func.count(tables.UserClueCount.id))
    count_secret_query = select(func.count(tables.SecretWord.id))
    count_subscription_query = select(func.count(tables.UserSubscription.id))
    count_hclue_query = select(func.count(tables.HotClue.id))
    count_history_query = select(func.count(tables.UserHistory.id))

    users, clue_counts, secrets, subscriptions, hclues, histories, latest_history = [
        []
    ] * 7
    latest_history = None

    with hs_transaction(session=dest_session, expire_on_commit=False) as session:
        existing_users = session.execute(user_query).scalars().all()
        total_existing_users = session.execute(count_user_query).scalar_one()

        existing_clue_counts = session.execute(clue_count_query).scalars().all()
        total_existing_clue_counts = session.execute(
            count_clue_count_query
        ).scalar_one()

        existing_secrets = session.execute(secret_query).scalars().all()
        total_existing_secrets = session.execute(count_secret_query).scalar_one()

        existing_subscriptions = session.execute(subscription_query).scalars().all()
        total_existing_subscriptions = session.execute(
            count_subscription_query
        ).scalar_one()

        existing_hclues = session.execute(hclue_query).scalars().all()
        total_existing_hclues = session.execute(count_hclue_query).scalar_one()

        existing_history = session.execute(history_query).scalars().all()
        total_existing_history = session.execute(count_history_query).scalar_one()

    existing_user_ids = {user.id for user in existing_users}
    existing_clue_counts_ids = {cc.id for cc in existing_clue_counts}
    existing_secret_ids = {s.id for s in existing_secrets}
    existing_subscription_ids = [s.id for s in existing_subscriptions]
    existing_hclue_ids = [hc.id for hc in existing_hclues]
    existing_history_ids = {h.id for h in existing_history}
    print(f"{datetime.datetime.now()} Got existing stuff, getting new stuff")

    with hs_transaction(session=origin_session, expire_on_commit=False) as session:
        users = [
            u
            for u in session.execute(user_query).scalars()
            if u.id not in existing_user_ids
        ]
        total_users = session.execute(count_user_query).scalar_one()
        print(
            f"total existing users: {total_existing_users:,}, total new users: {total_users:,}, diff : {total_users - total_existing_users:,}"
        )

        clue_counts = [
            cc
            for cc in session.execute(clue_count_query).scalars()
            if cc.id not in existing_clue_counts_ids
        ]
        total_clue_counts = session.execute(count_clue_count_query).scalar_one()
        print(
            f"total existing clue counts: {total_existing_clue_counts:,}, total new clue counts: {total_clue_counts:,}, diff : {total_clue_counts - total_existing_clue_counts:,}"
        )

        secrets = session.execute(secret_query).scalars().all()
        total_secrets = session.execute(count_secret_query).scalar_one()
        print(
            f"total existing secrets: {total_existing_secrets:,}, total new secrets: {total_secrets:,}, diff : {total_secrets - total_existing_secrets:,}"
        )

        subscriptions = session.execute(subscription_query).scalars().all()
        total_subscriptions = session.execute(count_subscription_query).scalar_one()
        print(
            f"total existing subscriptions: {total_existing_subscriptions:,}, total new subscriptions: {total_subscriptions:,}, diff : {total_subscriptions - total_existing_subscriptions:,}"
        )

        hclues = session.execute(hclue_query).scalars().all()
        total_hclues = session.execute(count_hclue_query).scalar_one()
        print(
            f"total existing hot clues: {total_existing_hclues:,}, total new hot clues: {total_hclues:,}, diff : {total_hclues - total_existing_hclues:,}"
        )

        histories = [
            history
            for history in session.execute(history_query).scalars()
            if history.id not in existing_history_ids
        ]
        latest_history = session.execute(
            select(tables.UserHistory).order_by(tables.UserHistory.id.desc()).limit(1)
        ).scalar_one()
        total_histories = latest_history.id
        print(
            f"total existing histories: {total_existing_history:,}, total new histories: {total_histories:,}, diff : {total_histories - total_existing_history:,}"
        )

    print(f"{datetime.datetime.now()} Got new stuff, filtering out existing stuff")
    users = [user for user in users if user.id not in existing_user_ids]
    secrets = [secret for secret in secrets if secret.id not in existing_secret_ids]
    subscriptions = [
        subs for subs in subscriptions if subs.id not in existing_subscription_ids
    ]
    hclues = [hclue for hclue in hclues if hclue.id not in existing_hclue_ids]
    print(f"{datetime.datetime.now()} Wow, that was a lot of filtering!")

    return users, clue_counts, secrets, subscriptions, hclues, histories, latest_history


users, clue_counts, secrets, subscriptions, hclues, histories, latest_history = (
    get_things_to_update()
)


print(f"Latest history id: {latest_history.id:,}")
if len(histories) > 0:
    print(f"Latest history we are inserting: {histories[-1].id:,}")


print("Starting to migrate:")
print(f"{len(users)} users")
print(f"{len(clue_counts)} clue_counts")
print(f"{len(secrets)} secrets")
print(f"{len(subscriptions)} subscriptions")
print(f"{len(hclues)} hot-clues")
dest_session = get_session(dest_db)
with hs_transaction(session=dest_session, expire_on_commit=False) as session:
    for user in tqdm.tqdm(users, desc="Users"):
        session.add(
            tables.User(
                id=user.id,
                email=user.email,
                user_type=user.user_type,
                active=user.active,
                picture=user.picture,
                given_name=user.given_name,
                family_name=user.family_name,
                first_login=user.first_login,
            )
        )
    for clue_count in tqdm.tqdm(clue_counts, desc="Clue Counts"):
        session.add(
            tables.UserClueCount(
                id=clue_count.id,
                user_id=clue_count.user_id,
                clue_count=clue_count.clue_count,
                game_date=clue_count.game_date,
            )
        )
    for secret in tqdm.tqdm(secrets, desc="Secrets"):
        session.add(
            tables.SecretWord(
                id=secret.id,
                word=secret.word,
                game_date=secret.game_date,
                solver_count=secret.solver_count,
            )
        )
    for subscription in tqdm.tqdm(subscriptions, desc="Subscriptions"):
        session.add(
            tables.UserSubscription(
                id=subscription.id,
                user_id=subscription.user_id,
                amount=subscription.amount,
                tier_name=subscription.tier_name,
                uuid=subscription.uuid,
                timestamp=subscription.timestamp,
            )
        )
    for hclue in tqdm.tqdm(hclues, desc="Hot Clues"):
        session.add(
            tables.HotClue(
                id=hclue.id,
                secret_word_id=hclue.secret_word_id,
                clue=hclue.clue,
            )
        )

chunk_size = 5_000
history_chuncks = [
    histories[i : i + chunk_size] for i in range(0, len(histories), chunk_size)
]
print(f"Inserting {len(histories):,} histories in {len(history_chuncks)} chunks")
for history_chunk in tqdm.tqdm(history_chuncks, desc="History Chunks"):
    with hs_transaction(session=dest_session) as session:
        for history in history_chunk:
            session.add(
                tables.UserHistory(
                    id=history.id,
                    user_id=history.user_id,
                    guess=history.guess,
                    similarity=history.similarity,
                    distance=history.distance,
                    egg=history.egg,
                    game_date=history.game_date,
                    solver_count=history.solver_count,
                )
            )

print("DONE!")
