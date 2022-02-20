SENTRY_SDK_URL = "https://0da75bab4671455ea1b7580cb93649f5@o444286.ingest.sentry.io/5645833"

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

RATE_LIMIT_WAIT_STATUS_MSG = "Waiting to resume after being rate limited. shippy will resume uploading in {} seconds."


CANNOT_CONTACT_SERVER_ERROR_MSG = "Cannot contact the server. "
UNEXPECTED_SERVER_RESPONSE_ERROR_MSG = "The server returned an unexpected response. "
FAILED_TO_RETRIEVE_SERVER_VERSION_ERROR_MSG = "Failed to retrieve server version information! "
FAILED_TO_LOG_IN_ERROR_MSG = "Failed to log into server! "

UNHANDLED_EXCEPTION_MSG = """
shippy crashed for an unknown reason. :(
To figure out what went wrong, please pass along the full output.
----
URL of request: {}
Request response code: {}
Request response: {}
---
"""
