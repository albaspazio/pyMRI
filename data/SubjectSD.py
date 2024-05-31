class SubjectSD:
    """
    This class represents a subject in the study data.

    Args:
        id (int): The unique identifier of the subject.
        label (str): The label of the subject.
        session (int): The session of the subject.

    Attributes:
        id (int): The unique identifier of the subject.
        label (str): The label of the subject.
        session (int): The session of the subject.

    """

    def __init__(self, id: int, label: str, session: int):
        self.id = id
        self.label = label
        self.session = session

    def is_equal(self, subj: 'SubjectSD') -> bool:
        """
        This function checks if two subjects are equal.

        Args:
            subj (SubjectSD): The subject to compare with.

        Returns:
            bool: True if the subjects are equal, False otherwise.

        """
        return subj.label == self.label and subj.session == self.session
