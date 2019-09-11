from pathlib import Path
from pkg_resources import resource_filename

def get_resource_filename(name):
    return Path(resource_filename(__name__, name))
