import argparse
import glob
import hashlib
import os.path

import requests
import semver
import sentry_sdk
from clint.textui import puts, colored

from .client import login_to_server, upload_to_server, get_server_version, get_md5_from_file
from .config import get_config_value, set_config_value
from .constants import *
from .exceptions import LoginException, UploadException
from .helper import input_yn, print_error_tag
from .version import __version__, server_compat_version

ignore_errors = [KeyboardInterrupt]

sentry_sdk.init(SENTRY_SDK_URL, traces_sample_rate=1.0, release=__version__, ignore_errors=ignore_errors)


def main():
    print("Welcome to shippy (v.{})!".format(__version__))

    parser = argparse.ArgumentParser(description="Client-side tool for interfacing with shipper.")
    parser.add_argument('-c', '--chunk-size', action='store_true', help='Edit chunk size')
    args = parser.parse_args()

    if args.chunk_size:
        edit_chunk_size()
        return

    # Check for updates
    check_shippy_update()

    try:
        server_url = get_config_value("shippy", "server")
        token = get_config_value("shipper", "token")
    except KeyError:
        print(FIRST_TIME_RUN_MSG)
        server_url = get_server_url()
        token = get_token(server_url)

    check_server_compat(server_url)

    chunked_upload = (get_config_value("shippy", "chunked_upload").lower() == "true")

    # Search current directory for files
    builds = get_builds_in_current_dir()

    if len(builds) == 0:
        print(NO_MATCHING_FILES_FOUND_ERROR_MSG)
    else:
        print("Detected {} build(s):".format(len(builds)))
        for build in builds:
            print("\t{}".format(build))

        if len(builds) > 1:
            puts(colored.red("Warning: you seem to be uploading multiple builds. "), newline=False)
            if not input_yn("Are you sure you want to continue?", default=False):
                return

        for build in builds:
            # Check build file validity
            if not check_build(build):
                print("Invalid build. Skipping...")
                continue

            if input_yn("Uploading build {}. Start?".format(build)):
                try:
                    upload_to_server(build, "{}.md5".format(build), server_url, token,
                                     use_chunked_upload=chunked_upload)
                except UploadException as exception:
                    print(exception)


def check_server_compat(server_url):
    print("shippy is contacting the remote server... Please wait.")
    server_version = get_server_version(server_url)
    if semver.compare(server_version, server_compat_version) == -1:
        print("Warning: the server you're connecting to is out-of-date. shippy may not work properly.")
        print("If you know the server admin, please ask them to upgrade the server.")
        print(" * Reported server version: \t{}".format(server_version))
        print(" * Compatible version: \t\t{}".format(server_compat_version))
        if not input_yn("Are you sure you want to continue? Only proceed if you know what you are doing!",
                        default=False):
            exit(0)
    else:
        print("Finished compatibility check. No problems found.")


def check_shippy_update():
    print("Checking for updates...")
    r = requests.get("https://api.github.com/repos/ericswpark/shippy/releases/latest")
    latest_version = r.json()['name']

    if semver.compare(__version__, latest_version) == -1:
        print("Warning: shippy is out-of-date. We recommend updating with the following command:")
        print("\tpip3 install --upgrade shipper-shippy")
    else:
        print("Finished update check. shippy is up-to-date!")


def get_builds_in_current_dir():
    builds = []
    glob_match = 'Bliss-v*.zip'

    print("Detecting builds in current directory...")

    for file in glob.glob(glob_match):
        builds.append(file)

    return builds


def check_build(filename):
    """ Makes sure the build is valid """
    print("Validating build {}...".format(filename))

    # Validate that there is a matching checksum file
    if not os.path.isfile("{}.md5".format(filename)):
        print("This build does not have a matching checksum file. ", end='')
        return False

    # Validate checksum
    print("Checking MD5 hash of {}... this may take a couple of seconds.".format(filename))
    md5_hash = hashlib.md5()
    with open(filename, "rb") as build_file:
        content = build_file.read()
        md5_hash.update(content)
    md5_hash = md5_hash.hexdigest()
    actual_hash = get_md5_from_file("{}.md5".format(filename))
    if md5_hash != actual_hash:
        print_error_tag()
        print("This build's checksum is invalid. ", end='')
        return False
    print("MD5 hash of {} matched.".format(filename))

    build_slug, _ = os.path.splitext(filename)
    _, _, _, build_type, build_variant, _ = build_slug.split('-')

    # Check build type
    if build_type != "OFFICIAL":
        print_error_tag()
        print("This build is not official. ", end='')
        return False

    # Check build variant
    valid_variants = ['gapps', 'vanilla', 'foss', 'goapps']
    if build_variant not in valid_variants:
        print_error_tag()
        print("This build has an unknown variant. ", end='')
        return False

    print("Validation of build {} complete. No problems found.".format(filename))
    return True


def get_server_url():
    server_url = input("Enter the server URL: ")

    while True:
        if "http" not in server_url:
            print_error_tag()
            # noinspection HttpUrlsUsage
            print("Server URL seems to be missing the schema. Please add http:// or https:// to the server URL.")
        else:
            break
        server_url = input("Enter the server URL: ")

    if server_url[-1] == '/':
        server_url = server_url[:-1]

    set_config_value("shippy", "server", server_url)

    return server_url


def get_token(server_url):
    while True:
        from getpass import getpass

        username = input("Enter your username: ")
        password = getpass(prompt="Enter your password: ")

        try:
            token = login_to_server(username, password, server_url)
            set_config_value("shipper", "token", token)
            return token
        except LoginException:
            puts(colored.red("An error occurred logging into the server. Please try again."))


def edit_chunk_size():
    print("Now editing the chunk size.")
    user_size = input("Specify the chunk size in megabytes: ")
    set_config_value("shippy", "chunked_upload_size", user_size * 1_000_000)


if __name__ == "__main__":
    main()
