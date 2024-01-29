
class SubjectListException(Exception):
    def __init__(self, msg, param):

        self.msg    = msg
        self.param  = param


class DataFileException(Exception):
    def __init__(self, msg, param):

        self.msg    = msg
        self.param  = param


class NotExistingImageException(Exception):
    def __init__(self, msg, image):

        self.msg    = msg
        self.image  = image
