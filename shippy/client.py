import hashlib
import os.path
import requests

from json import JSONDecodeError
from rich.console import Console
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
    UNEXPECTED_SERVER_RESPONSE_ERROR_MSG,
    RATE_LIMIT_WAIT_STATUS_MSG,
)
from .exceptions import LoginException, UploadException
from .helper import print_error

console = Console()

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
    transient=True,
)


def handle_undefined_response(request):
    """Handles undefined responses sent back by the server"""
    try:
        raise Exception(
            UNHANDLED_EXCEPTION_MSG.format(
                request.url, request.status_code, request.json()
            )
        )
    except JSONDecodeError:
        raise Exception(
            UNHANDLED_EXCEPTION_MSG.format(
                request.url, request.status_code, request.content
            )
        )


def get_server_version_info(server_url):
    """Gets server version information"""
    version_url = f"{server_url}/api/v1/system/info/"
    try:
        r = requests.get(version_url)
        if r.status_code == 200:
            return r.json()
        else:
            print_error(
                msg=FAILED_TO_RETRIEVE_SERVER_VERSION_ERROR_MSG,
                newline=True,
                exit_after=True,
            )
    except requests.exceptions.RequestException:
        print_error(
            msg=CANNOT_CONTACT_SERVER_ERROR_MSG
            + FAILED_TO_RETRIEVE_SERVER_VERSION_ERROR_MSG,
            newline=True,
            exit_after=True,
        )


def login_to_server(username, password, server_url):
    """Authenticates to server and returns authorization token"""
    login_url = f"{server_url}/api/v1/maintainers/login/"
    try:
        r = requests.post(login_url, data={"username": username, "password": password})

        if r.status_code == 200:
            data = r.json()
            return data["token"]
        elif r.status_code == 400 and r.json()["error"] == "blank_username_or_password":
            raise LoginException("Username or password must not be blank.")
        elif r.status_code == 404 and r.json()["error"] == "invalid_credential":
            raise LoginException("Invalid credentials!")
        # Really, really weird edge case where HTTP URLs would redirect and cause a
        # GET request
        elif (
            r.status_code == 405
            and r.json()["detail"] == 'Method "GET" not allowed.'
            and server_url[0:5] == "http:"
        ):
            print(
                "It seems like you entered a HTTP address when setting up shippy, but "
                "the server instance uses HTTPS. shippy automatically corrected your "
                "server URL in the configuration file."
            )
            server_url = f"https://{server_url[7:]}"
            set_config_value("shippy", "server", server_url)
            # Attempt logging in again
            return login_to_server(username, password, server_url)

        # Returned status code matches no scenario, abort
        handle_undefined_response(r)
    except LoginException as e:
        raise e
    except JSONDecodeError:
        print_error(
            msg=UNEXPECTED_SERVER_RESPONSE_ERROR_MSG + FAILED_TO_LOG_IN_ERROR_MSG,
            newline=True,
            exit_after=True,
        )
    except requests.exceptions.RequestException:
        print_error(
            msg=CANNOT_CONTACT_SERVER_ERROR_MSG + FAILED_TO_LOG_IN_ERROR_MSG,
            newline=True,
            exit_after=True,
        )


def check_token(server_url, token):
    token_check_url = f"{server_url}/api/v1/maintainers/token_check/"
    r = requests.get(token_check_url, headers={"Authorization": f"Token {token}"})

    if r.status_code == 200:
        print(f"Successfully validated token! Hello, {r.json()['username']}.")
        return True
    return False


def get_regex_pattern(server_url, token):
    regex_pattern_url = f"{server_url}/api/v1/maintainers/upload_filename_regex_pattern"
    r = requests.get(regex_pattern_url, headers={"Authorization": f"Token {token}"})

    if r.status_code == 200:
        return r.json()["pattern"]


def upload(server_url, build_file_path, token):
    """Upload given build files to specified server with token"""
    upload_url = f"{server_url}/api/v1/maintainers/chunked_upload/"

    chunk_size = 1000000  # 1 MB
    current_byte = 0
    total_file_size = os.path.getsize(build_file_path)

    with progress:
        upload_progress = progress.add_task(
            "[green]Uploading...", total=total_file_size
        )

        with open(build_file_path, "rb") as build_file:
            chunk_data = build_file.read(chunk_size)
            while chunk_data:
                try:
                    chunk_request = requests.put(
                        upload_url,
                        headers={
                            "Authorization": f"Token {token}",
                            "Content-Range": (
                                f"bytes {current_byte}-"
                                f"{current_byte + len(chunk_data) - 1}/{total_file_size}"
                            ),
                        },
                        data={"filename": build_file_path},
                        files={"file": chunk_data},
                    )

                    if chunk_request.status_code == 200:
                        upload_url = (
                            f"{server_url}/api/v1/maintainers/chunked_upload/"
                            f"{chunk_request.json()['id']}/"
                        )
                        current_byte += len(chunk_data)
                        progress.update(upload_progress, completed=current_byte)

                        # Read next chunk and continue
                        chunk_data = build_file.read(chunk_size)
                    elif chunk_request.status_code == 429:
                        print("shippy has been rate-limited.")
                        import re

                        wait_rate_limit(
                            int(re.findall(r"\d+", chunk_request.json()["detail"])[0])
                        )
                    elif int(chunk_request.status_code / 100) == 4:
                        try:
                            response_json = chunk_request.json()
                            raise UploadException(response_json["message"])
                        except KeyError:
                            raise UploadException(response_json)
                        except JSONDecodeError:
                            raise UploadException(
                                "Something went wrong during the upload."
                            )
                    else:
                        raise UploadException(
                            "An unidentified error occurred starting the upload."
                        )
                except requests.exceptions.RequestException:
                    raise UploadException(
                        "Something went wrong during the upload and the connection to "
                        "the server was lost!"
                    )

    # Finalize upload to begin processing
    try:
        with console.status(
            "Waiting for the server to process the uploaded build. This may take "
            "around 30 seconds... "
        ):
            # Check which hash we need to send over
            server_requests_checksum_type = get_server_version_info(
                server_url=server_url
            )["shippy_upload_checksum_type"]
            checksum_value = get_hash_of_file(
                build_file_path, checksum_type=server_requests_checksum_type
            )
            finalize_request = requests.post(
                upload_url,
                headers={"Authorization": f"Token {token}"},
                data={server_requests_checksum_type: checksum_value},
            )

            upload_exception_check(finalize_request, build_file_path)

            # Check if build should be disabled immediately after run
            check_build_disable(server_url, token, finalize_request.json()["build_id"])
    except UploadException as e:
        raise e
    except requests.exceptions.RequestException:
        raise UploadException(
            "Something went wrong during the upload and the connection to the server "
            "was lost!"
        )


def get_hash_of_file(filename, checksum_type):
    if checksum_type.lower() == "md5":
        hash_obj = hashlib.md5()
    elif checksum_type.lower() == "sha256":
        hash_obj = hashlib.sha256()
    else:
        # Unsupported checksum type
        return None

    with open(filename, "rb") as file:
        content = file.read()
        hash_obj.update(content)
    return hash_obj.hexdigest()


def get_hash_from_checksum_file(checksum_file):
    with open(checksum_file, "r") as checksum_file_raw:
        line = checksum_file_raw.readline()
        values = line.split(" ")
        return values[0]


def find_checksum_file(filename):
    valid_checksum_types = ["md5", "sha256"]
    has_checksum_file_type = None
    has_sum_postfix = False
    for checksum_type in valid_checksum_types:
        if os.path.isfile(f"{filename}.{checksum_type}"):
            has_checksum_file_type = checksum_type
            has_sum_postfix = False
        elif os.path.isfile(f"{filename}.{checksum_type}sum"):
            has_checksum_file_type = checksum_type
            has_sum_postfix = True
    return has_checksum_file_type, has_sum_postfix


def wait_rate_limit(s):
    import time

    with console.status(RATE_LIMIT_WAIT_STATUS_MSG.format(s)) as status:
        while s:
            time.sleep(1)
            s -= 1
            status.update(status=RATE_LIMIT_WAIT_STATUS_MSG.format(s))


def upload_exception_check(request, build_file):
    if request.status_code == 200:
        print(f"Successfully uploaded the build {build_file}!")
        return
    elif int(request.status_code / 100) == 4:
        try:
            response_json = request.json()
            raise UploadException(response_json["message"])
        except JSONDecodeError:
            raise UploadException("An unknown error occurred parsing the response.")
    elif int(request.status_code / 100) == 5:
        raise UploadException(
            "An internal server error occurred. Please contact the admins."
        )

    handle_undefined_response(request)


def check_build_disable(server_url, token, build_id):
    try:
        disable_build_on_upload = (
            get_config_value("shippy", "DisableBuildOnUpload") == "true"
        )
    except KeyError:
        # Not defined
        return

    if disable_build_on_upload:
        disable_build_url = (
            f"{server_url}/api/v1/maintainers/build/enabled_status_modify/"
        )
        r = requests.post(
            disable_build_url,
            headers={"Authorization": f"Token {token}"},
            data={"build_id": build_id, "enable": False},
        )

        if r.status_code == 200:
            print("Build has been automatically disabled, following configuration.")
            print("If this is unexpected, please check your configuration.")
        else:
            print("There was a problem disabling the build.")
