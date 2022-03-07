import os
import sys

THIS = os.path.realpath(__file__)
HERE = os.path.dirname(THIS)
BASE = os.path.dirname(HERE)


def parse_config_file(config, path):
    try:
        with open(path) as cfile:
            exec(cfile.read(), config)
        return True
    except Exception as exc:
        print('exec(%r) -> %s' % (path, exc))
        return False


parse_config_file(globals(), os.path.join(BASE, 'semantle.cfg'))

thismodule = sys.modules[__name__]
top_up_config = {
    'redis': 'REDISTOGO_URL',   # TODO: generic
    'api_key': 'API_KEY',
    'mongo': 'MONGODB',
    'model_v2_date': 'MODEL_V2_DATE',
}

for var, key in top_up_config.items():
    try:
        setattr(thismodule, var, os.environ[key])
    except KeyError:
        print('Could not configure %s: %s' % (var, key))
