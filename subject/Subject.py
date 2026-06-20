import os
from typing import List


class Subject:
    """
    Base Subject class representing a generic research subject with session tracking.
    
    This class provides fundamental subject management without MRI-specific dependencies.
    It establishes the contract for subject representation: each instance represents a 
    specific (label, sessid) pair.
    
    Attributes:
        label (str): The subject identifier/name (immutable after creation).
        sessid (int): The session number for this subject (immutable after creation).
        project: Reference to the parent Project instance.
        dir (str): The subject directory path (derived from project.subjects_dir, label, and sessid).
    """

    def __init__(self, label: str, project: 'Project', sessid: int = 1):
        """
        Initialize a new Subject instance.
        
        Args:
            label (str): The subject identifier/name.
            project (Project): The project object that this subject belongs to.
            sessid (int, optional): The session ID. Defaults to 1.
        """
        self.label = label
        self.sessid = sessid
        self.project = project

    @property
    def dir(self) -> str:
        """
        Get the subject-session directory path.
        
        Derived from project.subjects_dir, label, and sessid. This represents the
        filesystem location for this specific subject-session combination.
        
        Returns:
            str: The absolute path to the subject directory.
        """
        return os.path.join(self.project.subjects_dir, self.label, str(self.sessid))

    @property
    def exist(self) -> bool:
        """
        Check if the subject directory exists on the filesystem.
        
        Returns:
            bool: True if the directory exists, False otherwise.
        """
        return os.path.isdir(self.dir)

    def is_equal(self, subj: 'Subject') -> bool:
        """
        Check equality with another Subject.
        
        Two subjects are equal if they have the same label and sessid.
        
        Args:
            subj (Subject): The subject to compare with.
        
        Returns:
            bool: True if both subjects have identical label and sessid, False otherwise.
        """
        if subj is None:
            return False
        return subj.label == self.label and subj.sessid == self.sessid

    def is_in(self, subjects: List['Subject']) -> bool:
        """
        Check if this subject exists in a list of subjects.
        
        Args:
            subjects (List[Subject]): The list of subjects to search in.
        
        Returns:
            bool: True if a matching subject is found in the list, False otherwise.
        """
        if subjects is None or len(subjects) == 0:
            return False
        for subj in subjects:
            if self.is_equal(subj):
                return True
        return False

    def get_properties(self, sess: int = 1) -> 'Subject':
        """
        Create a new Subject instance with a different session.
        
        This creates a new Subject with the same label but a different session ID.
        Used for working with alternative sessions of the same subject.
        
        Args:
            sess (int, optional): The new session ID. Defaults to 1.
        
        Returns:
            Subject: A new Subject instance with the specified session.
        """
        return Subject(self.label, self.project, sess)

    def __repr__(self) -> str:
        """String representation of the Subject."""
        return f"Subject({self.label}, sess={self.sessid})"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.label}_sess{self.sessid}"
