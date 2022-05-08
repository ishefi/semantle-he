import os
import sys
from omegaconf import OmegaConf

OmegaConf.register_new_resolver("defau", lambda x, y: os.environ[x] if x in os.environ else y)

THIS = os.path.realpath(__file__)
HERE = os.path.dirname(THIS)
BASE = os.path.dirname(HERE)

thismodule = sys.modules[__name__]

from pathlib import Path

config_path = Path(BASE) / 'config.yaml'
if config_path.exists():
    conf = OmegaConf.load(str(config_path))
    for k, v in conf.items():
        setattr(thismodule, k, v)

if config := os.environ.get("HS_CONFIG"):
    exec(config, globals())
