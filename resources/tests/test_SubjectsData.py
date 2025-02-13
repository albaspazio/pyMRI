# Retrieve a column of values for all subjects when no SIDList is provided
import pandas as pd

from data.SubjectsData import SubjectsData
from data.SIDList import SIDList
from data.SID import SID

def test_retrieve_column_all_subjects():
    # Assuming SubjectsData is the class containing get_filtered_column
    subjects_data = SubjectsData()
    subjects_data.df = pd.DataFrame({'subj':["s1", "s2", "s3"], 'session':[1,1,1], 'age': [25, 30, 35]})
    # Mocking subjects attribute

    result = subjects_data.get_filtered_column(colname='age')

    assert result == [25, 30, 35]
    # assert labels == ['1', '2', '3']


# test_retrieve_column_all_subjects()


# Retrieve a column of values when all parameters are provided correctly
def test_retrieve_column_with_valid_parameters():

    subjects_data = SubjectsData()
    subjects_data.df = pd.DataFrame({'subj':["s1", "s2", "s3"], 'session':[1,1,1], 'age': [25, 30, 35]})

    # Execute
    result = subjects_data.get_subjects_column(colname='age')

    # Verify
    assert result == [10, 20]

test_retrieve_column_with_valid_parameters()