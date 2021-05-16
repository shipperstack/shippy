SENTRY_SDK_URL = "https://0da75bab4671455ea1b7580cb93649f5@o444286.ingest.sentry.io/5645833"

FIRST_TIME_RUN_MSG = """
It looks like this is your first time running shippy.
We need to configure shippy before you can use it.

"""

BETA_CHUNK_UPLOAD_PROMPT_MSG = """
[BETA] shippy has a new upload method that can improve upload performance and reliability.
Would you like to try it out? Answer no if you would like to use the traditional method of uploading.
"""

NO_MATCHING_FILES_FOUND_ERROR_MSG = """
No files matching the submission criteria were detected.

Please check the following:
  1. Make sure you are in the correct directory.
  2. Please do not rename the build artifacts.

If you believe this is a problem with shippy, please contact maintainer support.
"""