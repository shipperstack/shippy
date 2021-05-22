import configparser

from pathlib import Path

from shippy.constants import DEFAULT_SHIPPY_CHUNKED_UPLOAD_SIZE, DEFAULT_SHIPPY_CHUNKED_UPLOAD

home_dir = str(Path.home())

# Constants
CONFIGURATION_FILE = "{}/.shippy.ini".format(home_dir)

# Load configuration
config = configparser.ConfigParser()
config.read(CONFIGURATION_FILE)


def get_config_value(section, key):
    try:
        value = config[section][key]
    except KeyError:
        # Set defaults and return
        value = get_default(section, key)
        if value:
            set_config_value(section, key, value)
        else:
            raise KeyError

    return value


def get_default(section, key):
    if section == "shippy":
        if key == "chunked_upload":
            return DEFAULT_SHIPPY_CHUNKED_UPLOAD
        elif key == "chunked_upload_size":
            return str(DEFAULT_SHIPPY_CHUNKED_UPLOAD_SIZE)


def set_config_value(section, key, value):
    config_init()
    config[section][key] = value
    config_save()


def config_init():
    if not config.has_section('shippy'):
        config.add_section('shippy')
    if not config.has_section('shipper'):
        config.add_section('shipper')


def config_save():
    with open(CONFIGURATION_FILE, 'w+') as config_file:
        config.write(config_file)
