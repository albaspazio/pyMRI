
class SubjectListException(Exception):
    def __init__(self, method, param):

        self.method = method
        self.param = param