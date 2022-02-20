import os

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


parse_config_file(globals(), os.path.join(BASE, 'config.py'))

try:
    db = os.environ['JAWSDB_MARIA_URL']
    redis = os.environ['REDISTOGO_URL']
    api_key = os.environ['API_KEY']
except:
    pass
