import json
from pathlib import Path
from typing import Union


def get_config(path=None):
    if path is None:
        path = Path('config.json')
    abs_path = get_absolute_path(path)
    with abs_path.open() as f:
        config = json.load(f)
    return config


def get_absolute_path(path: Union[Path, str])-> Path:
    if isinstance(path, str):
        path = Path(path)
    if path.is_absolute():
        return path
    return Path(__file__).parent.resolve() / path
