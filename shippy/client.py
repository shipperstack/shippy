import os.path
from json import JSONDecodeError

import requests
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

from .config import get_config_value
from .exceptions import LoginException, UploadException
from .constants import UNHANDLED_EXCEPTION_MSG
from .helper import ProgressBar, print_error_tag

DEBUG = os.environ.get("SHIPPY_DEBUG", default=0)


def undef_response_exp(r):
    try:
        raise Exception(UNHANDLED_EXCEPTION_MSG.format(r.url, r.status_code, r.json()))
    except JSONDecodeError:
        raise Exception(UNHANDLED_EXCEPTION_MSG.format(r.url, r.status_code, r.content))


def get_server_version(server_url):
    """ Gets server version in semver format """
    version_url = "{}/maintainers/api/system/".format(server_url)
    r = requests.get(version_url)
    if r.status_code == 200:
        return r.json()['version']
    else:
        print_error_tag()
        print("Failed to retrieve server version information!")
        return None


def login_to_server(username, password, server_url):
    """ Logs in to server and returns authorization token """
    login_url = "{}/maintainers/api/login/".format(server_url)
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
        undef_response_exp(r)


def upload_to_server(build_file, checksum_file, server_url, token, use_chunked_upload=False):
    print("Uploading build {}...".format(build_file))

    if use_chunked_upload:
        print("Using chunked upload method to upload...")
        chunked_upload(server_url, build_file, checksum_file, token)
    else:
        print("Using direct upload method to upload...")
        direct_upload(server_url, build_file, checksum_file, token)


def chunked_upload(server_url, build_file, checksum_file, token):
    device_upload_url = "{}/maintainers/api/chunked_upload/".format(server_url)

    chunk_size = int(get_config_value("shippy", "chunked_upload_size"))
    current_index = 0
    total_file_size = os.path.getsize(build_file)

    bar = ProgressBar(expected_size=total_file_size, filled_char='=')

    with open(build_file, 'rb') as build_file_raw:
        while chunk_data := build_file_raw.read(chunk_size):
            r = requests.put(device_upload_url, headers={
                "Authorization": "Token {}".format(token),
                "Content-Range": "bytes {}-{}/{}".format(current_index, current_index + len(chunk_data) - 1,
                                                         total_file_size),
            }, data={"filename": build_file}, files={'file': chunk_data})

            if r.status_code == 200:
                device_upload_url = "{}/maintainers/api/chunked_upload/{}/".format(server_url, r.json()['id'])
                current_index += len(chunk_data)
                bar.show(current_index)
            elif r.status_code == 429:
                print("shippy has been rate-limited.")
                import re
                wait_rate_limit(int(re.findall("\d+", r.json()['detail'])[0]))
            else:
                if DEBUG:
                    print("Status code received from server: {}".format(r.status_code))
                    with open('output.html', 'wb') as error_output_raw:
                        error_output_raw.write(r.content)
                raise UploadException("Something went wrong during the upload.")

    print("")  # Clear progress bar from screen

    # Finalize upload to begin processing
    r = requests.post(device_upload_url, headers={"Authorization": "Token {}".format(token)},
                      data={'md5': get_md5_from_file(checksum_file)})

    upload_exception_check(r, build_file)


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


def direct_upload(server_url, build_file, checksum_file, token):
    device_upload_url = "{}/maintainers/api/upload/".format(server_url)

    e = MultipartEncoder(fields={
        'build_file': (build_file, open(build_file, 'rb'), 'text/plain'),
        'checksum_file': (checksum_file, open(checksum_file, 'rb'), 'text/plain'),
    })

    bar = ProgressBar(expected_size=e.len, filled_char='=')

    def callback(monitor):
        bar.show(monitor.bytes_read)

    m = MultipartEncoderMonitor(e, callback)

    r = requests.post(device_upload_url, headers={
        "Authorization": "Token {}".format(token),
        "Content-Type": e.content_type
    }, data=m)

    upload_exception_check(r, build_file)


def upload_exception_check(r, build_file):
    if DEBUG:
        print("Received code: {}".format(r.status_code))
        print(r.json())

    if r.status_code == 200:
        print("Successfully uploaded the build {}!".format(build_file))
        return
    elif r.status_code == 400:
        if r.json()['error'] == "duplicate_build":
            raise UploadException("This build already exists in the system!")
        elif r.json()['error'] == "missing_files":
            raise UploadException("One of the required fields are missing!")
        elif r.json()['error'] == "file_name_mismatch":
            raise UploadException("The build file name does not match the checksum file name!")
        elif r.json()['error'] == "invalid_file_name":
            raise UploadException("The file name was malformed!")
        elif r.json()['error'] == "not_official":
            raise UploadException("The build is not official!")
        elif r.json()['error'] == "codename_mismatch":
            raise UploadException("The codename does not match the build file name!")
    elif r.status_code == 401:
        if r.json()['error'] == "insufficient_permissions":
            raise UploadException("You are not allowed to upload for this device!")
    elif int(r.status_code / 100) == 5:
        raise UploadException("Something went wrong with the server. Please contact the admins.")

    undef_response_exp(r)
