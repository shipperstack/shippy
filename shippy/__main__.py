import semver
import sentry_sdk

from .exceptions import LoginException, UploadException
from .helper import input_yn
from .client import login_to_server, upload_to_server, get_server_version
from .config import get_config_value, set_config_value
from .constants import *
from .version import __version__, server_compat_version

ignore_errors = [KeyboardInterrupt]

sentry_sdk.init(SENTRY_SDK_URL, traces_sample_rate=1.0, release=__version__, ignore_errors=ignore_errors)


def main():
    print("Welcome to shippy (v.{})!".format(__version__))

    try:
        server_url = get_config_value("shippy", "server")
        token = get_config_value("shipper", "token")
    except KeyError:
        print(FIRST_TIME_RUN_MSG)
        server_url = input("Enter the server URL: ")

        while True:
            if "http" not in server_url:
                print("Server URL seems to be missing the schema. Please add http:// or https:// to the server URL.")
            else:
                break
            server_url = input("Enter the server URL: ")

        if server_url[-1] == '/':
            print("Trailing slash found. shippy automatically removed it for you!")
            server_url = server_url[:-1]

        set_config_value("shippy", "server", server_url)
        server_url = server_url

        check_server_compat(server_url)

        while True:
            from getpass import getpass

            username = input("Enter your username: ")
            password = getpass(prompt="Enter your password: ")

            try:
                token = login_to_server(username, password, server_url)
                set_config_value("shipper", "token", token)
                break
            except LoginException:
                print("An error occurred logging into the server. Please try again.")

    check_server_compat(server_url)

    try:
        chunked_upload = (get_config_value("shippy", "chunked_upload") == "true")
    except KeyError:
        # Ask preference for beta upload method
        if input_yn(BETA_CHUNK_UPLOAD_PROMPT_MSG):
            set_config_value("shippy", "chunked_upload", "true")
        else:
            set_config_value("shippy", "chunked_upload", "false")
        chunked_upload = (get_config_value("shippy", "chunked_upload") == "true")

    # Search current directory for files
    import glob

    glob_match = 'Bliss-v*.zip'
    build_count = len(glob.glob(glob_match))
    builds = []

    if build_count == 0:
        print(NO_MATCHING_FILES_FOUND_ERROR_MSG)
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
                    while True:
                        try:
                            upload_to_server(build, "{}.md5".format(build), server_url, token,
                                             use_chunked_upload=chunked_upload)
                            break
                        except UploadException as exception:
                            print(exception)
                            if input_yn("An error occurred uploading the build {}. "
                                        "Do you want to try again?".format(build)):
                                continue
                            else:
                                break


def check_server_compat(server_url):
    server_version = get_server_version(server_url)
    if semver.compare(server_version, server_compat_version) == -1:
        print("Warning: the server you're connecting to is out-of-date. shippy may not work properly.")
        print("If you know the server admin, please ask them to upgrade the server.")
        print("Reported version from server: {}".format(server_version))
        print("Compatible version: {}\n".format(server_compat_version))


if __name__ == "__main__":
    main()
