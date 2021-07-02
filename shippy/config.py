import configparser

from pathlib import Path

home_dir = str(Path.home())

# Constants
CONFIGURATION_FILE = "{}/.shippy.ini".format(home_dir)

# Load configuration
config = configparser.ConfigParser()
config.read(CONFIGURATION_FILE)


def get_config_value(section, key):
    return config[section][key]


def get_optional_true_config_value(section, key):
    try:
        value = (config[section][key] == "true")
        return value
    except KeyError:
        # Set default to false so users can change it later
        set_config_value(section, key, "false")
        return False


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
