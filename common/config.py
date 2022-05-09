import os
import sys
from omegaconf import OmegaConf
from pathlib import Path

thismodule = sys.modules[__name__]

conf = OmegaConf.create()
if (config_path := Path(__file__).parent.parent.resolve() / 'config.yaml').exists():
    conf.merge_with(OmegaConf.load(str(config_path)))
if yaml_str := os.environ.get('YAML_CONFIG_STR'):
    conf.merge_with(OmegaConf.create(yaml_str))
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
