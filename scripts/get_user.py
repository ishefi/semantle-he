#!/user/bin/env python
import argparse
import os
import sys

base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend([base])

from common.session import get_session
from logic.user_logic import UserLogic


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Get user information")
    parser.add_argument("email", help="Email of the user")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    print(f"Getting user information for {args.email}")
    user_logic = UserLogic(get_session())
    user = await user_logic.get_user(args.email)
    if user is None:
        print(f"User with email {args.email} not found")
    else:
        print(user)
        print(f"User subsciption expiry: {user_logic.get_subscription_expiry(user)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
