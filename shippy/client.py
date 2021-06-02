import os.path
from json import JSONDecodeError

import requests

from .exceptions import LoginException, UploadException
from .constants import UNHANDLED_EXCEPTION_MSG, FAILED_TO_RETRIEVE_SERVER_VERSION_ERROR_MSG, \
    CANNOT_CONTACT_SERVER_ERROR_MSG, FAILED_TO_LOG_IN_ERROR_MSG
from .helper import ProgressBar, print_error


def handle_undefined_response(request):
    try:
        raise Exception(UNHANDLED_EXCEPTION_MSG.format(request.url, request.status_code, request.json()))
    except JSONDecodeError:
        raise Exception(UNHANDLED_EXCEPTION_MSG.format(request.url, request.status_code, request.content))


def get_server_version(server_url):
    """ Gets server version in semver format """
    version_url = "{}/maintainers/api/system/".format(server_url)
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
    login_url = "{}/maintainers/api/login/".format(server_url)
    try:
        r = requests.post(login_url, data={'username': username, 'password': password})

        if r.status_code == 200:
            data = r.json()
            return data['token']
        elif r.status_code == 400:
            if r.json()['error'] == "blank_username_or_password":
                raise LoginException("Username or password must not be blank.")
        elif r.status_code == 404:
            if r.json()['error'] == "invalid_credential":
                raise LoginException("Invalid credentials!")
        else:
            handle_undefined_response(r)
    except LoginException as e:
        raise e
    except requests.exceptions.RequestException:
        print_error(msg=CANNOT_CONTACT_SERVER_ERROR_MSG + FAILED_TO_LOG_IN_ERROR_MSG, newline=True, exit_after=True)


def upload(server_url, build_file, checksum_file, token):
    device_upload_url = "{}/maintainers/api/chunked_upload/".format(server_url)

    chunk_size = 10_000_000  # 10 MB
    current_index = 0
    total_file_size = os.path.getsize(build_file)

    bar = ProgressBar(expected_size=total_file_size, filled_char='=')

    with open(build_file, 'rb') as build_file_raw:
        while chunk_data := build_file_raw.read(chunk_size):
            try:
                chunk_request = requests.put(device_upload_url, headers={
                    "Authorization": "Token {}".format(token),
                    "Content-Range": "bytes {}-{}/{}".format(current_index, current_index + len(chunk_data) - 1,
                                                             total_file_size),
                }, data={"filename": build_file}, files={'file': chunk_data})

                if chunk_request.status_code == 200:
                    device_upload_url = "{}/maintainers/api/chunked_upload/{}/".format(server_url,
                                                                                       chunk_request.json()['id'])
                    current_index += len(chunk_data)
                    bar.show(current_index)
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
        raise UploadException("Generic upload error. Make sure your device exists within shipper (contact an admin!)")
    elif int(request.status_code / 100) == 5:
        raise UploadException("Something went wrong with the server. Please contact the admins.")

    handle_undefined_response(request)
