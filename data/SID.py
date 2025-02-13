

class SID:
    """
    This class allows to uniquely identify a subject session (thus a specific folder in the mri file system)
    and its row in the pandas dataframe containing its demographic/clinical/behavioral data
    While specific lists of subjects can be loaded, data in DataProject and its inner structure SubjectsData are loaded at once.
    thus their id is fixed.

    Args:
        id (int): The unique identifier of the subject.
        label (str): The label of the subject.
        session (int): The session of the subject.

    Attributes:
        id (int): The unique identifier of the subject.
        label (str): The label of the subject.
        session (int): The session of the subject.

    """

    def __init__(self, label: str, session: int, id: int):
        self.id = id
        self.label = label
        self.session = session

    def is_equal(self, subj: 'SID') -> bool:
        """
        This function checks if two subjects are equal.

        Args:
            subj (SID): The subject to compare with.

        Returns:
            bool: True if the subjects are equal, False otherwise.

        """
        return subj.label == self.label and subj.session == self.session
