#!/usr/bin/env python
import argparse
import asyncio
import datetime
import os
import sys
import uuid

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])
from common import schemas
from common.session import get_session
from logic.user_logic import UserLogic


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add subscription")
    parser.add_argument("--email", type=str, help="User email", required=True)
    parser.add_argument("--amount", type=int, help="Amount of subscription", default=3)
    parser.add_argument("--message_id", type=str, help="Message ID")

    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    user_logic = UserLogic(get_session())

    subscription = schemas.Subscription(
        verification_token="",
        message_id=args.message_id or uuid.uuid4().hex,
        timestamp=datetime.datetime.now(datetime.UTC),
        email=args.email,
        amount=args.amount,
        tier_name=None,
    )
    success = await user_logic.subscribe(subscription)
    if not success:
        print("Failed to add subscription")
        return
    else:
        user = await user_logic.get_user(args.email)
        if user is None:
            print("No such user")
            return
        expiry = user_logic.get_subscription_expiry(user)
        print(
            f"Subscription of {args.amount} added successfully to user {args.email}, "
            f"expires on {expiry}"
        )


if __name__ == "__main__":
    asyncio.run(main())
