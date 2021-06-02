SENTRY_SDK_URL = "https://0da75bab4671455ea1b7580cb93649f5@o444286.ingest.sentry.io/5645833"

FIRST_TIME_RUN_MSG = """
It looks like this is your first time running shippy.
We need to configure shippy before you can use it.

"""

NO_MATCHING_FILES_FOUND_ERROR_MSG = """
No files matching the submission criteria were detected.

Please check the following:
  1. Make sure you are in the correct directory.
  2. Please do not rename the build artifacts.

If you believe this is a problem with shippy, please contact maintainer support.
"""

SERVER_COMPAT_ERROR_MSG = """
The server you're connecting to is out-of-date.
If you know the server admin, please ask them to upgrade the server.
 * Reported server version: \t{}
 * Compatible version: \t\t{}
 
To prevent data corruption, shippy will not work with an outdated server. Exiting...
"""

SHIPPY_OUTDATED_MSG = """
Warning: shippy is out-of-date.
 * Current version: \t{}
 * New version: \t{}

We recommend updating shippy with the following command:
\tpip3 install --upgrade shipper-shippy
"""

CANNOT_CONTACT_SERVER_ERROR_MSG = "Cannot contact the server. "
FAILED_TO_RETRIEVE_SERVER_VERSION_ERROR_MSG = "Failed to retrieve server version information!"
FAILED_TO_LOG_IN_ERROR_MSG = "Failed to log into server!"

UNHANDLED_EXCEPTION_MSG = """
shippy crashed for an unknown reason. :(
To figure out what went wrong, please pass along the full output.
----
URL of request: {}
Request response code: {}
Request response: {}
---
"""
