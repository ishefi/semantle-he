import json
import pathlib


def get_config(path=None):
    if path is None:
        path = pathlib.Path(__file__).parent.resolve() / pathlib.Path('config.json')
    path = pathlib.Path(path)
    with path.open() as f:
        config = json.load(f)
    return config
