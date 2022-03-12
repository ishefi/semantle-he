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

