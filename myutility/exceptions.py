
class SubjectListException(Exception):
    """
    Exception class for SubjectList operations.

    Attributes:
        msg (str): Error message.
        param (str): Parameter associated with the error.
    """

    def __init__(self, msg, param):
        self.msg = msg
        self.param = param


class DataFileException(Exception):
    """
    Exception class for data file operations.

    Attributes:
        msg (str): Error message.
        param (str): Parameter associated with the error.
    """

    def __init__(self, msg, param=None):
        self.msg = msg
        self.param = param


class NotExistingImageException(Exception):
    """
    Exception class for when an image does not exist.

    Attributes:
        msg (str): Error message.
        image (str): Image name.
    """

    def __init__(self, msg, image):
        self.msg = msg
        self.image = image
