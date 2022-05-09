import os
import sys
from omegaconf import OmegaConf
from pathlib import Path

THIS = os.path.realpath(__file__)
HERE = os.path.dirname(THIS)
BASE = os.path.dirname(HERE)

thismodule = sys.modules[__name__]



config_path = Path(BASE) / 'config.yaml'
if config_path.exists():
    conf = OmegaConf.load(str(config_path))
    for k, v in conf.items():
        setattr(thismodule, k, v)

def get_top_ups(conf):
    top_ups = ""
    for key, value in conf.items():
        if key.startswith('hs_top_up_'):
            kkey = key.replace('hs_top_up_', '')
            try:
                top_ups += "%s = %r\n" % (kkey, os.environ[value])
            except KeyError:
                print('Could not configure %s: %s' % (key, value))
    return top_ups

if config := os.environ.get("HS_CONFIG"):
    exec(config, globals())
    top_ups = get_top_ups(globals())
    exec(top_ups, globals())
