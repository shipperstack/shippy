import argparse
import glob
import hashlib
import os.path

import semver
import sentry_sdk

from .client import login_to_server, upload_to_server, get_server_version, get_md5_from_file
from .config import get_config_value, set_config_value
from .constants import *
from .exceptions import LoginException, UploadException
from .helper import input_yn
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
    print("Detecting builds in current directory...")
    glob_match = 'Bliss-v*.zip'
    build_count = len(glob.glob(glob_match))
    builds = []

    if build_count == 0:
        print(NO_MATCHING_FILES_FOUND_ERROR_MSG)
    else:
        print("Detected build(s):")
        for file in glob.glob(glob_match):
            print("\t{}".format(file))
            builds.append(file)

        for build in builds:
            # Check build file validity
            if not check_build(build):
                print("Invalid build. Skipping...")
                continue

            if input_yn("Uploading build {}. Start?".format(build)):
                while True:
                    # noinspection PyBroadException
                    try:
                        upload_to_server(build, "{}.md5".format(build), server_url, token,
                                         use_chunked_upload=chunked_upload)
                        break
                    except UploadException as exception:
                        print(exception)
                        if exception.retry:
                            if input_yn("An error occurred uploading the build {}. "
                                        "Do you want to try again?".format(build)):
                                continue
                            else:
                                break
                        else:
                            break
                    except Exception as exception:
                        print("An unknown exception occurred. Please report this to the developers.")
                        raise exception


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


def check_build(filename):
    """ Makes sure the build is valid """
    # Validate that there is a matching checksum file
    if not os.path.isfile("{}.md5".format(filename)):
        print("This build does not have a matching checksum file. ", end='')
        return False

    # Validate checksum
    md5_hash = hashlib.md5()
    with open(filename, "rb") as build_file:
        content = build_file.read()
        md5_hash.update(content)
    md5_hash = md5_hash.hexdigest()
    actual_hash = get_md5_from_file("{}.md5".format(filename))
    if md5_hash != actual_hash:
        print("This build's checksum is invalid. ", end='')
        return False

    build_slug, _ = os.path.splitext(filename)
    _, _, _, build_type, build_variant, _ = build_slug.split('-')

    # Check build type
    if build_type != "OFFICIAL":
        print("This build is not official. ", end='')
        return False

    # Check build variant
    valid_variants = ['gapps', 'vanilla', 'foss', 'goapps']
    if build_variant not in valid_variants:
        print("This build has an unknown variant. ", end='')
        return False

    return True


def get_server_url():
    server_url = input("Enter the server URL: ")

    while True:
        if "http" not in server_url:
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
            print("An error occurred logging into the server. Please try again.")


def edit_chunk_size():
    print("Now editing the chunk size.")
    user_size = input("Specify the chunk size in megabytes: ")
    set_config_value("shippy", "chunked_upload_size", user_size * 1_000_000)


if __name__ == "__main__":
    main()
