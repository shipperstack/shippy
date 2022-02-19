import os.path
import requests

from json import JSONDecodeError
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from .config import get_config_value, set_config_value
from .constants import (
    UNHANDLED_EXCEPTION_MSG,
    FAILED_TO_RETRIEVE_SERVER_VERSION_ERROR_MSG,
    CANNOT_CONTACT_SERVER_ERROR_MSG,
    FAILED_TO_LOG_IN_ERROR_MSG,
    UNEXPECTED_SERVER_RESPONSE_ERROR_MSG
)
from .exceptions import LoginException, UploadException
from .helper import print_error

# Set up progress bar
progress = Progress(
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
    transient=True
)


def handle_undefined_response(request):
    try:
        raise Exception(UNHANDLED_EXCEPTION_MSG.format(request.url, request.status_code, request.json()))
    except JSONDecodeError:
        raise Exception(UNHANDLED_EXCEPTION_MSG.format(request.url, request.status_code, request.content))


def get_server_version(server_url):
    """ Gets server version in semver format """
    version_url = "{}/api/v1/system/info/".format(server_url)
    try:
        r = requests.get(version_url)
        if r.status_code == 200:
            return r.json()['version']
        else:
            print_error(msg=FAILED_TO_RETRIEVE_SERVER_VERSION_ERROR_MSG, newline=True, exit_after=True)
    except requests.exceptions.RequestException:
        print_error(msg=CANNOT_CONTACT_SERVER_ERROR_MSG + FAILED_TO_RETRIEVE_SERVER_VERSION_ERROR_MSG, newline=True,
                    exit_after=True)


def login_to_server(username, password, server_url):
    """ Logs in to server and returns authorization token """
    login_url = "{}/api/v1/maintainers/login/".format(server_url)
    try:
        r = requests.post(login_url, data={'username': username, 'password': password})

        if r.status_code == 200:
            data = r.json()
            return data['token']
        elif r.status_code == 400 and r.json()['error'] == "blank_username_or_password":
            raise LoginException("Username or password must not be blank.")
        elif r.status_code == 404 and r.json()['error'] == "invalid_credential":
            raise LoginException("Invalid credentials!")
        # Really, really weird edge case where HTTP URLs would redirect and cause a GET request
        elif r.status_code == 405 and r.json()['detail'] == 'Method "GET" not allowed.' and server_url[0:5] == "http:":
            print("It seems like you entered a HTTP address when setting up shippy, but the server instance uses "
                  "HTTPS. shippy automatically corrected your server URL in the configuration file.")
            server_url = "https://{}".format(server_url[7:])
            set_config_value("shippy", "server", server_url)
            # Attempt logging in again
            return login_to_server(username, password, server_url)

        # Returned status code matches no scenario, abort
        handle_undefined_response(r)
    except LoginException as e:
        raise e
    except JSONDecodeError:
        print_error(msg=UNEXPECTED_SERVER_RESPONSE_ERROR_MSG + FAILED_TO_LOG_IN_ERROR_MSG, newline=True, exit_after=True)
    except requests.exceptions.RequestException:
        print_error(msg=CANNOT_CONTACT_SERVER_ERROR_MSG + FAILED_TO_LOG_IN_ERROR_MSG, newline=True, exit_after=True)


def check_token(server_url, token):
    token_check_url = "{}/api/v1/maintainers/token_check/".format(server_url)
    r = requests.get(token_check_url, headers={"Authorization": "Token {}".format(token)})

    if r.status_code == 200:
        print("Successfully validated token! Hello, {}.".format(r.json()['username']))
        return True
    return False


def upload(server_url, build_file, checksum_file, token):
    device_upload_url = "{}/api/v1/maintainers/chunked_upload/".format(server_url)

    chunk_size = 10000000  # 10 MB
    current_index = 0
    total_file_size = os.path.getsize(build_file)

    with progress:
        upload_progress = progress.add_task("[green]Uploading...", total=total_file_size)

        with open(build_file, 'rb') as build_file_raw:
            chunk_data = build_file_raw.read(chunk_size)
            while chunk_data:
                try:
                    chunk_request = requests.put(device_upload_url, headers={
                        "Authorization": "Token {}".format(token),
                        "Content-Range": "bytes {}-{}/{}".format(current_index, current_index + len(chunk_data) - 1,
                                                                total_file_size),
                    }, data={"filename": build_file}, files={'file': chunk_data})

                    if chunk_request.status_code == 200:
                        device_upload_url = "{}/api/v1/maintainers/chunked_upload/{}/".format(server_url,
                                                                                            chunk_request.json()['id'])
                        current_index += len(chunk_data)
                        progress.update(upload_progress, completed=current_index)
                        
                        # Read next chunk and continue
                        chunk_data = build_file_raw.read(chunk_size)
                    elif chunk_request.status_code == 429:
                        print("shippy has been rate-limited.")
                        import re
                        wait_rate_limit(int(re.findall("\d+", chunk_request.json()['detail'])[0]))
                    else:
                        raise UploadException("Something went wrong during the upload.")
                except requests.exceptions.RequestException:
                    raise UploadException("Something went wrong during the upload and the connection to the server was "
                                        "lost!")

    print("")  # Clear progress bar from screen

    # Finalize upload to begin processing
    try:
        finalize_request = requests.post(device_upload_url, headers={"Authorization": "Token {}".format(token)},
                                         data={'md5': get_md5_from_file(checksum_file)})

        upload_exception_check(finalize_request, build_file)

        # Check if build should be disabled immediately after run
        check_build_disable(server_url, token, finalize_request.json()['build_id'])
    except UploadException as e:
        raise e
    except requests.exceptions.RequestException:
        raise UploadException("Something went wrong during the upload and the connection to the server was lost!")


def get_md5_from_file(checksum_file):
    with open(checksum_file, 'r') as checksum_file_raw:
        line = checksum_file_raw.readline()
        values = line.split(" ")
        return values[0]


def wait_rate_limit(seconds):
    import time
    while seconds:
        print("Will resume in {} seconds...".format(seconds), end='\r')
        time.sleep(1)
        seconds -= 1
    print(end='\x1b[2K\r')


def upload_exception_check(request, build_file):
    if request.status_code == 200:
        print("Successfully uploaded the build {}!".format(build_file))
        return
    elif request.status_code == 400:
        if request.json()['error'] == "duplicate_build":
            raise UploadException("This build already exists in the system!")
        elif request.json()['error'] == "missing_files":
            raise UploadException("One of the required fields are missing!")
        elif request.json()['error'] == "file_name_mismatch":
            raise UploadException("The build file name does not match the checksum file name!")
        elif request.json()['error'] == "invalid_file_name":
            raise UploadException("The file name was malformed!")
        elif request.json()['error'] == "not_official":
            raise UploadException("The build is not official!")
        elif request.json()['error'] == "codename_mismatch":
            raise UploadException("The codename does not match the build file name!")
    elif request.status_code == 401:
        if request.json()['error'] == "insufficient_permissions":
            raise UploadException("You are not allowed to upload for this device!")
    elif request.status_code == 404:
        raise UploadException("Your device isn't registered on shipper. Please contact an admin to add your device.")
    elif int(request.status_code / 100) == 5:
        raise UploadException("An internal server error occurred. Please contact the admins.")

    handle_undefined_response(request)


def check_build_disable(server_url, token, build_id):
    try:
        disable_build_on_upload = (get_config_value("shippy", "DisableBuildOnUpload") == "true")
    except KeyError:
        # Not defined
        return

    if disable_build_on_upload:
        disable_build_url = "{}/api/v1/maintainers/build/enabled_status_modify/".format(server_url)
        r = requests.post(disable_build_url, headers={"Authorization": "Token {}".format(token)},
                          data={"build_id": build_id, "enable": False})

        if r.status_code == 200:
            print("Build has been automatically disabled, following configuration.")
            print("If this is unexpected, please check your configuration.")
        else:
            print("There was a problem disabling the build.")
