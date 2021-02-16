import configparser
import sys

from version import *
from helper import input_yn
from client import login_to_server, upload_to_server
from settings import DEBUG

from pathlib import Path

# Get user home directory
home_dir = str(Path.home())

# Define constants
TOKEN = ""
CONFIGURATION_FILE = "{}/.shippy.ini".format(home_dir)

def exception_handler(exception_type, exception, traceback, debug_hook=sys.excepthook):
    if DEBUG:
        debug_hook(exception_type, exception, traceback)
    else:
        print("%s: %s" % (exception_type.__name__, exception))


sys.excepthook = exception_handler


def main():
    global TOKEN

    # Load configuration file
    config = configparser.ConfigParser()
    config.read(CONFIGURATION_FILE)

    print("Welcome to shippy {} (version code {})!".format(VERSION_STRING, VERSION_CODE))

    try:
        TOKEN = config['shipper']['token']
    except KeyError:
        print("""
It looks like this is your first time running shippy.
In the next couple of steps, shippy will ask for your username
and password and fetch the authentication token from the shipper server.
This token will be saved in {}. Let's get started!
        """.format(CONFIGURATION_FILE))

        config.add_section('shipper')

        while True:
            from getpass import getpass

            username = input("Enter your username: ")
            password = getpass(prompt="Enter your password: ")

            try:
                config['shipper']['token'] = TOKEN = login_to_server(username, password)

                with open(CONFIGURATION_FILE, 'w+') as config_file:
                    config.write(config_file)
                break
            except:
                print("An error occurred logging into the server. Please try again.")

    # Search current directory for files
    import glob

    glob_match = 'Bliss-v*.zip'
    build_count = len(glob.glob(glob_match))
    builds = []

    if build_count == 0:
        print("""
Oops, no files were detected! Are you sure you are in the correct directory?
Please do not rename the build artifacts. This breaks a lot of systems.
If you have a unique case contact maintainer support.
        """)
    else:
        if build_count == 1:
            print("Detected the following build:")
        else:
            print("Detected the following builds:")
        for file in glob.glob(glob_match):
            print("\t{}".format(file))
            builds.append(file)

        for build in builds:
            # Check if build has md5 file
            import os.path
            if not os.path.isfile("{}.md5".format(build)):
                print("We couldn't find a valid checksum file for this build! Skipping....")
            else:
                if input_yn("Uploading build {}. Start?".format(build)):
                    upload_to_server(build, "{}.md5".format(build))


if __name__ == "__main__":
    main()
