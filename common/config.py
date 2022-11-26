import os
import sys
from omegaconf import OmegaConf
from pathlib import Path

thismodule = sys.modules[__name__]

conf = OmegaConf.create()
if (config_path := Path(__file__).parent.parent.resolve() / 'config.yaml').exists():
    conf.merge_with(OmegaConf.load(config_path))
if yaml_str := os.environ.get('YAML_CONFIG_STR'):
    conf.merge_with(OmegaConf.create(yaml_str))
for k, v in conf.items():
    setattr(thismodule, k, v)
