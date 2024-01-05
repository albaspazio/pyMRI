class SubjectSD:
    def __init__(self, id:int, label:str, session:int):
        self.id         = id
        self.label      = label
        self.session    = session

    def is_equal(self, subj:'SubjectSD'):
        return subj.label == self.label and subj.id == self.id and subj.session == self.session
