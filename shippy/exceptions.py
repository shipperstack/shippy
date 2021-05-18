
class LoginException(Exception):
    pass


class UploadException(Exception):
    def __init__(self, retry=True, **data):
        self.retry = retry
        self.data = data
