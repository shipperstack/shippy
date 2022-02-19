# shippy
![version](https://img.shields.io/github/v/release/ericswpark/shippy)
![commits-since](https://img.shields.io/github/commits-since/ericswpark/shippy/latest)
[
![PyPI](https://img.shields.io/pypi/v/shipper-shippy)
![PyPI - Downloads](https://img.shields.io/pypi/dm/shipper-shippy)
](https://pypi.org/project/shipper-shippy/)

Client-side tool to interface with shipper

# Usage

Get shippy from PyPI:

```shell
pip3 install --upgrade shipper-shippy
```

Go to the directory with build files, and run:

```shell
shippy
```

Command-line arguments:

```shell
usage: __main__.py [-h] [-y]

Client-side tool for interfacing with shipper

optional arguments:
  -h, --help  show this help message and exit
  -y, --yes   Upload builds automatically without prompting
```

# Configuration

shippy stores its configuration in `~/.shippy.ini`. An example configuration file is shown below:

```ini
[shippy]
server = https://example.com
token = a1b2c3d4e5...
DisableBuildOnUpload = false
UploadWithoutPrompt = false
```

Configuration options explained:

### `server`
Server URL

### `token`
Token used to sign in to the server

### `DisableBuildOnUpload`
Immediately disables the build after uploading it. Useful if you are uploading from Jenkins or uploading potentially
unstable builds. Do NOT use under normal circumstances!

### `UploadWithoutPrompt`
shippy will not prompt you before uploading builds, and will automatically upload all builds found in the current
directory. Use with caution. Same as the `-y`/`--yes` flag shown above.
