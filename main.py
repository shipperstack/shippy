import sentry_sdk

from exceptions import LoginException, UploadException
from version import *
from helper import input_yn
from client import login_to_server, upload_to_server
from config import get_config_value, set_config_value


ignore_errors = [KeyboardInterrupt]

sentry_sdk.init(
    "https://0da75bab4671455ea1b7580cb93649f5@o444286.ingest.sentry.io/5645833",
    traces_sample_rate=1.0,
    release=VERSION_STRING,
    ignore_errors=ignore_errors
)


# Define constants
TOKEN = ""
SERVER_URL = ""


def main():
    global TOKEN, SERVER_URL
    print("Welcome to shippy (v.{})!".format(VERSION_STRING))

    try:
        SERVER_URL = get_config_value("shippy", "server")
        TOKEN = get_config_value("shipper", "token")
    except KeyError:
        print("It looks like this is your first time running shippy.")
        print("We need to configure shippy before you can use it.")
        print("Please enter the server URL.")
        server_url = input("Enter the server URL: ")

        if server_url[-1] == '/':
            print("Trailing slash found. shippy automatically removed it for you!")
            server_url = server_url[:-1]

        set_config_value("shippy", "server", server_url)
        SERVER_URL = server_url

        while True:
            from getpass import getpass

            username = input("Enter your username: ")
            password = getpass(prompt="Enter your password: ")

            try:
                TOKEN = login_to_server(username, password, server_url)
                set_config_value("shipper", "token", TOKEN)
                break
            except LoginException:
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
                    while True:
                        try:
                            upload_to_server(build, "{}.md5".format(build), SERVER_URL, TOKEN)
                            break
                        except UploadException:
                            if input_yn("An error occurred uploading the build {}. Do you want to try again?".format(build)):
                                continue


if __name__ == "__main__":
    main()
