from typing import Any


class SubjectListException(Exception):
    """
    Exception class for SubjectList operations.

    Attributes:
        msg (str): Error message.
        param (str): Parameter associated with the error.
    """

    def __init__(self, msg, param:Any=None):
        self.msg = msg
        self.param = param

class SubjectExistException(Exception):
    """
    Exception class raise when a requested subject session does not exist in the file system.

    Attributes:
        msg (str): Error message.
        param (str): Parameter associated with the error.
    """

    def __init__(self, msg, param:Any=None):
        self.msg = msg
        self.param = param

class DataFileException(Exception):
    """
    Exception class for Subject data access operations.

    Attributes:
        msg (str): Error message.
        param (str): Parameter associated with the error.
    """

    def __init__(self, msg, param:Any=None):
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
