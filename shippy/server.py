import hashlib
import os.path
import requests

from json import JSONDecodeError

import semver
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from loguru import logger

from .constants import (
    UNHANDLED_EXCEPTION_MSG,
    FAILED_TO_RETRIEVE_SERVER_VERSION_ERROR_MSG,
    RATE_LIMIT_WAIT_STATUS_MSG,
    RATE_LIMIT_MSG,
    UNKNOWN_UPLOAD_ERROR_MSG,
    UNKNOWN_UPLOAD_START_ERROR_MSG,
    WAITING_FINALIZATION_MSG,
    CHUNK_SIZE,
)
from .exceptions import LoginException, UploadException
from .version import server_compat_version, __version__

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


def log_debug_request_send(request_type, url, headers=None, data=None):
    logger.debug(
        f"Sending {request_type} request to {url}, with header {headers} and data {data}"
    )


def log_debug_request_response(r):
    try:
        r_content = r.json()
    except ValueError:
        r_content = r.content

    logger.debug(f"Received response: {r_content}")


class Server:
    def __init__(self, url, token=None):
        self.url = url
        self.token = token

    def is_url_secure(self):
        return self.url[0:5] == "https"

    def is_server_compatible(self):
        server_compat = semver.VersionInfo.parse(server_compat_version)
        return self.get_version() >= server_compat

    def is_shippy_compatible(self):
        shippy_version = semver.VersionInfo.parse(__version__)
        return shippy_version >= self.get_shippy_compat_version()

    def login(self, username, password):
        r = self._post(
            url="/api/v1/maintainers/login",
            data={"username": username, "password": password},
        )

        if r.status_code == 200:
            self.token = r.json()["token"]
        elif r.status_code == 400 and r.json()["error"] == "blank_username_or_password":
            raise LoginException("Username or password must not be blank.")
        elif r.status_code == 404 and r.json()["error"] == "invalid_credential":
            raise LoginException("Invalid credentials!")
        elif r.status_code == 301 and not self.is_url_secure():
            raise LoginException("Server uses HTTPS, but was supplied HTTP URL.")
        else:
            handle_undefined_response(r)

    def get_version(self):
        return semver.VersionInfo.parse(self._get_info()["version"])

    def get_shippy_compat_version(self):
        return semver.VersionInfo.parse(self._get_info()["shippy_compat_version"])

    def _get_info(self):
        r = self._get(url="/api/v1/system/info")
        if r.status_code == 200:
            return r.json()
        else:
            raise Exception(FAILED_TO_RETRIEVE_SERVER_VERSION_ERROR_MSG)

    def get_regex_pattern(self):
        r = self._get(
            url="/api/v1/maintainers/upload_filename_regex_pattern",
            headers=self._get_header(),
        )

        if r.status_code == 200:
            return r.json()["pattern"]

    def _get_checksum_type(self):
        return self._get_info()["shippy_upload_checksum_type"]

    def get_username(self):
        r = self._get(
            url="/api/v1/maintainers/token_check/",
            headers=self._get_header(),
        )

        return r.json()["username"]

    def is_token_valid(self):
        r = self._get(
            url="/api/v1/maintainers/token_check/",
            headers=self._get_header(),
        )

        return r.status_code == 200

    def upload(self, build_path):
        current_byte = 0
        upload_id = ""
        total_file_size = os.path.getsize(build_path)

        with progress:
            upload_progress = progress.add_task(
                "[green]Uploading...", total=total_file_size
            )

            # Check if there is a previous upload attempt
            previous_attempts = self._get(
                url="/api/v1/maintainers/chunked_upload/", headers=self._get_header()
            ).json()
            for attempt in previous_attempts:
                if build_path == attempt["filename"]:
                    logger.debug(
                        f"Found a previous upload attempt for the build {build_path}, "
                        f"created on {attempt['created_at']}",
                    )
                    current_byte = attempt["offset"]
                    upload_id = attempt["id"]

            with open(build_path, "rb") as build_file:
                build_file.seek(current_byte)
                chunk = build_file.read(CHUNK_SIZE)
                while chunk:
                    try:
                        r = self._upload_chunk(
                            build_path=build_path,
                            chunk=chunk,
                            current=current_byte,
                            total=total_file_size,
                            upload_id=upload_id,
                        )

                        if r.status_code == 200:
                            upload_id = r.json()["id"]
                            current_byte += len(chunk)
                            progress.update(upload_progress, completed=current_byte)

                            # Read next chunk and continue
                            chunk = build_file.read(CHUNK_SIZE)
                        elif r.status_code == 429:
                            upload_handle_rate_limit(r)
                        elif int(r.status_code / 100) == 4:
                            upload_handle_4xx_response(r)
                        else:
                            raise UploadException(UNKNOWN_UPLOAD_START_ERROR_MSG)
                    except requests.exceptions.RequestException:
                        raise UploadException(UNKNOWN_UPLOAD_ERROR_MSG)

        # Finalize upload to begin processing
        try:
            with console.status(WAITING_FINALIZATION_MSG):
                checksum = get_hash_of_file(
                    build_path, checksum_type=self._get_checksum_type()
                )
                r = self._upload_finalize(upload_id=upload_id, checksum=checksum)

                upload_exception_check(r, build_path)
        except UploadException as e:
            raise e
        except requests.exceptions.RequestException:
            raise UploadException(UNKNOWN_UPLOAD_ERROR_MSG)

        return upload_id

    def disable_build(self, upload_id):
        r = self._post(
            "/api/v1/maintainers/build/enabled_status_modify/",
            headers=self._get_header(),
            data={"build_id": upload_id, "enable": False},
        )

        if r.status_code == 200:
            print(f"Build {upload_id} has been disabled.")
        else:
            raise Exception("There was a problem disabling the build.")

    def _upload_chunk(self, build_path, chunk, current, total, upload_id):
        if upload_id:
            url = f"/api/v1/maintainers/chunked_upload/{upload_id}/"
        else:
            url = "/api/v1/maintainers/chunked_upload/"
        result = self._put(
            url=url,
            headers=self._get_header(chunk=chunk, current=current, total=total),
            data={"filename": build_path},
            files={"file": chunk},
        )
        logger.debug(f"Got back: {result}")
        return result

    def _upload_finalize(self, upload_id, checksum):
        return self._post(
            url=f"/api/v1/maintainers/chunked_upload/{upload_id}/",
            headers=self._get_header(),
            data={self._get_checksum_type(): checksum},
        )

    def _get_header(self, chunk=None, current=None, total=None):
        header = {"Authorization": f"Token {self.token}"}

        if chunk is not None and current is not None and total is not None:
            header[
                "Content-Range"
            ] = f"bytes {current}-{current + len(chunk) - 1}/{total}"

        return header

    def _post(self, url, headers=None, data=None):
        log_debug_request_send(
            request_type="POST", url=f"{self.url}{url}", headers=headers, data=data
        )
        r = requests.post(
            url=f"{self.url}{url}", headers=headers, data=data, allow_redirects=False
        )
        log_debug_request_response(r)
        return r

    def _get(self, url, headers=None, data=None):
        log_debug_request_send(
            request_type="GET", url=f"{self.url}{url}", headers=headers, data=data
        )
        r = requests.get(url=f"{self.url}{url}", headers=headers, data=data)
        log_debug_request_response(r)
        return r

    def _put(self, url, headers, data, files):
        log_debug_request_send(
            request_type="PUT", url=f"{self.url}{url}", headers=headers, data=data
        )
        r = requests.put(
            url=f"{self.url}{url}", headers=headers, data=data, files=files
        )
        log_debug_request_response(r)
        return r


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


def upload_handle_rate_limit(chunk_request):
    print(RATE_LIMIT_MSG)
    import re

    wait_rate_limit(int(re.findall(r"\d+", chunk_request.json()["detail"])[0]))


def upload_handle_4xx_response(chunk_request):
    try:
        response_json = chunk_request.json()
        raise UploadException(response_json["message"])
    except (KeyError, JSONDecodeError):
        raise UploadException(UNKNOWN_UPLOAD_ERROR_MSG)


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
