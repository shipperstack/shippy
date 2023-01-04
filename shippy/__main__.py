import argparse
import re
import glob
import os.path

import requests
import semver
import sentry_sdk

from rich import print
from rich.console import Console

from .client import (
    login_to_server,
    upload,
    get_server_version_info,
    get_regex_pattern,
    get_hash_from_checksum_file,
    check_token,
    get_hash_of_file,
    find_checksum_file,
)
from .config import get_config_value, set_config_value, get_optional_true_config_value
from .constants import (
    SENTRY_SDK_URL,
    SERVER_COMPAT_ERROR_MSG,
    SHIPPY_COMPAT_ERROR_MSG,
    SHIPPY_OUTDATED_MSG,
)
from .exceptions import LoginException, UploadException
from .helper import input_yn, print_error, print_warning, print_success
from .version import __version__, server_compat_version

ignore_errors = [KeyboardInterrupt, ConnectionError]

sentry_sdk.init(
    SENTRY_SDK_URL,
    traces_sample_rate=1.0,
    release=__version__,
    ignore_errors=ignore_errors,
)

console = Console()


def main():
    print(f"Welcome to shippy (v.{__version__})!")

    # Check if we cannot prompt the user (default to auto-upload)
    upload_without_prompt = get_optional_true_config_value(
        "shippy", "UploadWithoutPrompt"
    )

    # Get commandline arguments
    args = init_argparse()
    upload_without_prompt = upload_without_prompt or args.yes

    # Check for updates
    check_shippy_update()

    # Check if server config is valid
    server_url, token = check_server_config_validity()

    # Check server version compatibility
    check_server_compat(server_url)

    # Get regex pattern from server
    regex_pattern = get_regex_pattern(server_url=server_url, token=token)

    # Search current directory for files
    builds = get_builds_in_current_dir(regex_pattern)

    if len(builds) == 0:
        print_error(
            msg="No files matching the submission criteria were detected in the "
            "current directory.",
            newline=True,
            exit_after=False,
        )
    else:
        print(f"Detected {len(builds)} build(s):")
        for build in builds:
            print(f"\t{build}")

        if not upload_without_prompt and len(builds) > 1:
            print_warning("You seem to be uploading multiple builds. ", newline=False)
            if not input_yn("Are you sure you want to continue?", default=False):
                return

        for build in builds:
            # Check build file validity
            if not check_build(build):
                print_warning("Invalid build. Skipping...")
                continue

            if upload_without_prompt or input_yn(f"Uploading build {build}. Start?"):
                try:
                    upload(server_url=server_url, build_file_path=build, token=token)
                except UploadException as exception:
                    print_error(exception, newline=True, exit_after=False)


def check_server_config_validity():
    try:
        server_url = get_config_value("shippy", "server")
        if not check_server_url_schema(server_url):
            print_error(
                msg="The configuration file is corrupt. Please delete it and restart "
                    "shippy.",
                newline=True,
                exit_after=True,
            )

        token = get_config_value("shippy", "token")

        token = check_token_validity(server_url, token)
    except KeyError:
        print_warning(
            "No configuration file found or configuration is invalid. You need to "
            "configure shippy before you can start using it."
        )
        server_url = get_server_url()
        token = get_token(server_url)

        # In case login function updated server URL, we need to fetch it again
        server_url = get_config_value("shippy", "server")
    return server_url, token


def init_argparse():
    parser = argparse.ArgumentParser(
        description="Client-side tool for interfacing with shipper"
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Upload builds automatically without prompting",
    )
    return parser.parse_args()


def check_server_compat(server_url):
    with console.status(
        "Please wait while shippy contacts the remote server to check compatibility... "
    ):
        server_version_info = get_server_version_info(server_url)

    # Check if shipper version is compatible
    if semver.compare(server_version_info["version"], server_compat_version) == -1:
        print_error(
            msg=SERVER_COMPAT_ERROR_MSG.format(
                server_version_info["version"], server_compat_version
            ),
            newline=True,
            exit_after=True,
        )

    # Check if shippy version is compatible, but only if running stable builds
    if is_prerelease():
        print_warning(
            "You're running a prerelease build of shippy. Server compatibility checks "
            "are disabled."
        )
    else:
        if semver.compare(server_version_info["shippy_compat_version"], __version__) == 1:
            print_error(
                msg=SHIPPY_COMPAT_ERROR_MSG.format(
                    server_version_info["shippy_compat_version"], __version__
                ),
                newline=True,
                exit_after=True,
            )

    print_success("Finished compatibility check. No problems found.")


def check_token_validity(server_url, token):
    with console.status(
        "Please wait while shippy contacts the remote server to check if the token is "
        "still valid... "
    ):
        is_token_valid = check_token(server_url, token)

    if not is_token_valid:
        # Token check failed, prompt for login again
        print_warning("The saved token is invalid. Please sign-in again.")
        token = get_token(server_url)
    return token


def check_shippy_update():
    with console.status("Please wait while shippy checks for updates... "):
        r = requests.get(
            "https://api.github.com/repos/shipperstack/shippy/releases/latest"
        )
        latest_version = r.json()["name"]
    
    # Check if user is running an alpha/beta build
    if is_prerelease():
        print_warning(
            "You're running a prerelease build of shippy. Be careful as prerelease "
            "versions can behave in unexpected ways! If you haven't been instructed "
            "to test shippy, please consider switching back to a stable build."
        )
    else:
        # User is running a stable build, proceed with update check
        if semver.compare(__version__, latest_version) == -1:
            print(SHIPPY_OUTDATED_MSG.format(__version__, latest_version))
        else:
            print_success("Finished update check. shippy is up-to-date!")


def is_prerelease():
    return "a" in __version__ or "b" in __version__


def get_builds_in_current_dir(regex_pattern):
    with console.status("Detecting builds in current directory..."):
        builds = []
        files = [f for f in glob.glob("*.zip")]
        for file in files:
            if re.search(regex_pattern, file):
                builds.append(file)

        return builds


def check_build(filename):
    """Makes sure the build is valid"""
    print(f"Validating build {filename}...")

    # Validate that there is a matching checksum file
    has_checksum_file_type, has_sum_postfix = find_checksum_file(filename=filename)

    if has_checksum_file_type is None:
        print_warning(
            "This build does not have a matching checksum file. ", newline=False
        )
        return False

    # Validate checksum
    with console.status(
        f"Checking {has_checksum_file_type.upper()} hash of {filename}... this may "
        "take a couple of seconds. "
    ):
        hash_val = get_hash_of_file(
            filename=filename, checksum_type=has_checksum_file_type
        )
        if not has_sum_postfix:
            actual_hash_val = get_hash_from_checksum_file(
                f"{filename}.{has_checksum_file_type}"
            )
        else:
            actual_hash_val = get_hash_from_checksum_file(
                f"{filename}.{has_checksum_file_type}sum"
            )
        if hash_val != actual_hash_val:
            print_error(
                msg="This build's checksum is invalid. ",
                newline=False,
                exit_after=False,
            )
            return False
        print_success(f"{has_checksum_file_type.upper()} hash of {filename} matched.")

    build_slug, _ = os.path.splitext(filename)
    _, _, _, build_type, build_variant, _ = build_slug.split("-")

    # Check build type
    if build_type != "OFFICIAL":
        print_error(msg="This build is not official. ", newline=False, exit_after=False)
        return False

    # Check build variant
    valid_variants = ["gapps", "vanilla", "foss", "goapps"]
    if build_variant not in valid_variants:
        print_error(
            msg="This build has an unknown variant. ", newline=False, exit_after=False
        )
        return False

    print_success(f"Validation of build {filename} complete. No problems found.")
    return True


def get_server_url():
    try:
        while True:
            server_url = input("Enter the server URL: ")
            if not check_server_url_schema(server_url):
                # noinspection HttpUrlsUsage
                print_error(
                    msg="Server URL is missing either http:// or https://.",
                    newline=True,
                    exit_after=False,
                )
            else:
                break

        if server_url[-1] == "/":
            server_url = server_url[:-1]

        set_config_value("shippy", "server", server_url)

        return server_url
    except KeyboardInterrupt:
        exit(0)


def check_server_url_schema(url):
    return "http" in url


def get_token(server_url):
    while True:
        from getpass import getpass

        try:
            username = input("Enter your username: ")
            password = getpass(prompt="Enter your password: ")

            try:
                token = login_to_server(username, password, server_url)
                set_config_value("shippy", "token", token)
                return token
            except LoginException as exception:
                print_error(
                    f"{exception} Please try again.", newline=True, exit_after=False
                )
        except KeyboardInterrupt:
            exit(0)


if __name__ == "__main__":
    main()
