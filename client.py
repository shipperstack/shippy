from clint.textui.progress import Bar as ProgressBar
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

import requests

def login_to_server(username, password, server_url):
    """ Logs in to server and returns authorization token """
    LOGIN_URL = "{}/maintainers/api/login/".format(server_url)
    r = requests.post(LOGIN_URL, data={'username': username, 'password': password})

    if r.status_code == 200:
        data = r.json()
        return data['token']
    elif r.status_code == 400:
        raise Exception("Username or password must not be blank.")
    elif r.status_code == 404:
        raise Exception("Invalid credentials!")
    else:
        raise Exception("An unknown error occurred.")


def upload_to_server(build_file, checksum_file, server_url, token):
    import os.path
    # Get codename from build_file
    build_file_name, _ = os.path.splitext(build_file)
    try:
        _, _, codename, _, _, _ = build_file_name.split('-')
    except:
        raise Exception("The file name is mangled!")

    # Get device ID from server
    DEVICE_ID_URL = "{}/maintainers/api/device/id/".format(server_url)
    print("Fetching device ID for device {}...".format(codename))
    r = requests.get(DEVICE_ID_URL, headers={"Authorization": "Token {}".format(token)}, data={"codename": codename})

    if r.status_code == 200:
        data = r.json()
        device_id = data['id']
    elif r.status_code == 400:
        raise Exception("The device with the specified codename does not exist.")
    elif r.status_code == 401:
        raise Exception("You are not authorized to upload with this device.")
    else:
        raise Exception("A problem occurred while querying the device ID.")

    print("Uploading build {}...".format(build_file))

    device_upload_url = "{}/maintainers/api/device/{}/upload/".format(server_url, device_id)

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

    print(r.json())

    if r.status_code == 200:
        print("Successfully uploaded the build {}!".format(build_file))
    elif r.status_code == 400:
        if r.json()['error'] == "duplicate_build":
            raise Exception("This build already exists in the system!")
        raise Exception("One of the required fields are missing!")
    elif r.status_code == 401:
        raise Exception("You are not allowed to upload for the device {}!".format(codename))
    elif r.status_code == 500:
        raise Exception("An internal server error occurred. Contact the administrators for help.")
    else:
        raise Exception("A problem occurred while uploading your build.")