import argparse
import re
import glob
import os.path
import signal
from json import JSONDecodeError
from loguru import logger

import requests
import semver
import sentry_sdk

from rich import print
from rich.console import Console

from .server import (
    get_hash_from_checksum_file,
    get_hash_of_file,
    find_checksum_file,
    Server,
)
from .config import get_config_value, set_config_value, get_optional_true_config_value
from .constants import (
    SENTRY_SDK_URL,
    SERVER_COMPAT_ERROR_MSG,
    SHIPPY_COMPAT_ERROR_MSG,
    SHIPPY_OUTDATED_MSG,
    UNEXPECTED_SERVER_RESPONSE_ERROR_MSG,
    FAILED_TO_LOG_IN_ERROR_MSG,
    CANNOT_CONTACT_SERVER_ERROR_MSG,
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


# Handle SIGINT gracefully and don't puke up traceback
def sigint_handler(*_):
    exit(1)


signal.signal(signal.SIGINT, sigint_handler)


def main():
    # Get commandline arguments
    args = init_argparse()

    if args.debug:
        print_warning("Debug mode has been turned on!")
        logger.add(sink="shippy_{time}.log", level="DEBUG", enqueue=True)

    print(f"Welcome to shippy (v.{__version__})!")

    # Check for updates
    check_shippy_update()

    # Initialize server
    server = build_server_from_config()
    check_server_compat(server)
    check_token_validity(server)

    # Search current directory for files with regex pattern returned by server
    build_paths = get_builds_in_current_dir(server.get_regex_pattern())

    if len(build_paths) == 0:
        print_error(
            msg="No files matching the submission criteria were detected in the "
            "current directory.",
            newline=True,
            exit_after=False,
        )
    else:
        print(f"Detected {len(build_paths)} build(s):")
        for build_path in build_paths:
            print(f"\t{build_path}")

        if not is_upload_without_prompt_enabled(args) and len(build_paths) > 1:
            print_warning("You seem to be uploading multiple builds. ", newline=False)
            if not input_yn("Are you sure you want to continue?", default=False):
                return

        for build_path in build_paths:
            # Check build file validity
            if not check_build(build_path):
                print_warning("Invalid build. Skipping...")
                continue

            if is_upload_without_prompt_enabled(args) or input_yn(
                f"Uploading build {build_path}. Start?"
            ):
                try:
                    upload_id = server.upload(build_path=build_path)

                    if is_build_disabling_enabled():
                        server.disable_build(upload_id=upload_id)
                except UploadException as exception:
                    print_error(exception, newline=True, exit_after=False)


def is_upload_without_prompt_enabled(args):
    config_value = get_optional_true_config_value(
        "shippy", "UploadWithoutPrompt"
    )

    return config_value or args.yes


def build_server_from_config():
    try:
        url = get_config_value("shippy", "server")
        if not check_server_url_schema(url):
            print_error(
                msg="The configuration file is corrupt. Please delete it and restart "
                "shippy.",
                newline=True,
                exit_after=True,
            )

        token = get_config_value("shippy", "token")
        server = Server(url=url, token=token)
    except KeyError:
        print_warning(
            "No configuration file found or configuration is invalid. You need to "
            "configure shippy before you can start using it."
        )
        server = Server(url=get_server_url())
        prompt_login(server)
    return server


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
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    return parser.parse_args()


def check_server_compat(server):
    with console.status(
        "Please wait while shippy contacts the remote server to check compatibility... "
    ):
        # Check if shipper version is compatible
        if semver.compare(server.get_version(), server_compat_version) == -1:
            print_error(
                msg=SERVER_COMPAT_ERROR_MSG.format(
                    server.get_version(), server_compat_version
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
        if semver.compare(server.get_shippy_compat_version(), __version__) == 1:
            print_error(
                msg=SHIPPY_COMPAT_ERROR_MSG.format(
                    server.get_shippy_compat_version(), __version__
                ),
                newline=True,
                exit_after=True,
            )

    print_success("Finished compatibility check. No problems found.")


def check_token_validity(server):
    with console.status(
        "Please wait while shippy contacts the remote server to check if the token is "
        "still valid... "
    ):
        if server.is_token_valid():
            print_success(
                f"Successfully validated token! Hello, {server.get_username()}!"
            )
        else:
            # Token check failed, prompt for login again
            print_warning("The saved token is invalid. Please sign-in again.")
            prompt_login(server)


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
    with console.status(f"Checking {has_checksum_file_type.upper()} hash..."):
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
        print_success(f"Success!")

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
            msg="This build has an unknown variant. ",
            newline=False,
            exit_after=False,
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


def prompt_login(server):
    while True:
        from getpass import getpass

        try:
            username = input("Enter your username: ")
            password = getpass(prompt="Enter your password: ")

            try:
                server.login(username=username, password=password)
                set_config_value("shippy", "token", server.token)
            except LoginException as exception:
                print_error(
                    f"{exception} Please try again.", newline=True, exit_after=False
                )
            except JSONDecodeError:
                print_error(
                    msg=UNEXPECTED_SERVER_RESPONSE_ERROR_MSG
                    + FAILED_TO_LOG_IN_ERROR_MSG,
                    newline=True,
                    exit_after=True,
                )
            except requests.exceptions.RequestException:
                print_error(
                    msg=CANNOT_CONTACT_SERVER_ERROR_MSG + FAILED_TO_LOG_IN_ERROR_MSG,
                    newline=True,
                    exit_after=True,
                )
        except KeyboardInterrupt:
            exit(0)


def is_build_disabling_enabled():
    try:
        return get_config_value("shippy", "DisableBuildOnUpload") == "true"
    except KeyError:
        return False


if __name__ == "__main__":
    main()
