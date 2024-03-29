
class SubjectListException(Exception):
    def __init__(self, method, param):

        self.method = method
        self.param = param


class DataFileException(Exception):
    def __init__(self, method, param):

        self.method = method
        self.param = param


class NotExistingImageException(Exception):
    def __init__(self, method, path):

        self.method = method
        self.path = path
