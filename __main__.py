#!/usr/bin/env python
from argparse import ArgumentParser
from itertools import pairwise

import uvicorn


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--no-reload", action="store_false")
    args, unknown_args = parser.parse_known_args()
    uvicorn_kwargs = {
        "host": args.host,
        "reload": args.no_reload,
        "port": args.port,
    }
    for arg1, arg2 in pairwise(unknown_args):
        if not arg1.startswith("--"):
            parser.error(f"Unknow arg: {arg1}")
        else:
            uvicorn_kwargs[arg1[2:]] = arg2

    uvicorn.run("app:app", **uvicorn_kwargs)


if __name__ == "__main__":
    main()
