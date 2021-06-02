import glob
import hashlib
import os.path

import requests
import semver
import sentry_sdk

from .client import login_to_server, upload, get_server_version, get_md5_from_file
from .config import get_config_value, set_config_value
from .constants import *
from .exceptions import LoginException, UploadException
from .helper import input_yn, print_error, print_warning
from .version import __version__, server_compat_version

ignore_errors = [KeyboardInterrupt]

sentry_sdk.init(SENTRY_SDK_URL, traces_sample_rate=1.0, release=__version__, ignore_errors=ignore_errors)


def main():
    print("Welcome to shippy (v.{})!".format(__version__))

    # Check for updates
    check_shippy_update()

    try:
        server_url = get_config_value("shippy", "server")
        token = get_config_value("shipper", "token")
    except KeyError:
        print("No configuration file found. You need to configure shippy before you can start using it.")
        server_url = get_server_url()
        token = get_token(server_url)

    check_server_compat(server_url)

    # Search current directory for files
    builds = get_builds_in_current_dir()

    if len(builds) == 0:
        print_error(msg="No files matching the submission criteria were detected in the current directory.",
                    newline=True, exit_after=False)
    else:
        print("Detected {} build(s):".format(len(builds)))
        for build in builds:
            print("\t{}".format(build))

        if len(builds) > 1:
            print_warning("Warning: you seem to be uploading multiple builds. ", newline=False)
            if not input_yn("Are you sure you want to continue?", default=False):
                return

        for build in builds:
            # Check build file validity
            if not check_build(build):
                print("Invalid build. Skipping...")
                continue

            if input_yn("Uploading build {}. Start?".format(build)):
                try:
                    upload(server_url=server_url,
                           build_file=build,
                           checksum_file="{}.md5".format(build),
                           token=token)
                except UploadException as exception:
                    print(exception)


def check_server_compat(server_url):
    print("shippy is contacting the remote server... Please wait.")
    server_version = get_server_version(server_url)
    if semver.compare(server_version, server_compat_version) == -1:
        print_error(msg=SERVER_COMPAT_ERROR_MSG.format(server_version, server_compat_version), newline=True,
                    exit_after=True)
        exit(0)
    else:
        print("Finished compatibility check. No problems found.")


def check_shippy_update():
    print("Checking for updates...")
    r = requests.get("https://api.github.com/repos/ericswpark/shippy/releases/latest")
    latest_version = r.json()['name']

    if semver.compare(__version__, latest_version) == -1:
        print(SHIPPY_OUTDATED_MSG.format(__version__, latest_version))
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
        print_error(msg="This build's checksum is invalid. ", newline=False, exit_after=False)
        return False
    print("MD5 hash of {} matched.".format(filename))

    build_slug, _ = os.path.splitext(filename)
    _, _, _, build_type, build_variant, _ = build_slug.split('-')

    # Check build type
    if build_type != "OFFICIAL":
        print_error(msg="This build is not official. ", newline=False, exit_after=False)
        return False

    # Check build variant
    valid_variants = ['gapps', 'vanilla', 'foss', 'goapps']
    if build_variant not in valid_variants:
        print_error(msg="This build has an unknown variant. ", newline=False, exit_after=False)
        return False

    print("Validation of build {} complete. No problems found.".format(filename))
    return True


def get_server_url():
    try:
        server_url = input("Enter the server URL: ")

        while True:
            if "http" not in server_url:
                # noinspection HttpUrlsUsage
                print_error(msg="Server URL is missing either http:// or https://.", newline=True, exit_after=False)
            else:
                break
            server_url = input("Enter the server URL: ")

        if server_url[-1] == '/':
            server_url = server_url[:-1]

        set_config_value("shippy", "server", server_url)

        return server_url
    except KeyboardInterrupt:
        exit(0)


def get_token(server_url):
    while True:
        from getpass import getpass

        try:
            username = input("Enter your username: ")
            password = getpass(prompt="Enter your password: ")

            try:
                token = login_to_server(username, password, server_url)
                set_config_value("shipper", "token", token)
                return token
            except LoginException as exception:
                print_error("{} Please try again.".format(exception), newline=True, exit_after=False)
        except KeyboardInterrupt:
            exit(0)


if __name__ == "__main__":
    main()
