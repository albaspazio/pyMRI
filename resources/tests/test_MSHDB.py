# Adding new subjects to an empty database should return a database with those subjects
import pandas

from data.MSHDB import MSHDB
from data.Sheets import Sheets
from data.SubjectsData import SubjectsData


def test_add_new_subjects_to_empty_db():
    # Initialize an empty MSHDB instance
    empty_db = MSHDB(file_schema='test_mshdb_schema.json')
    empty_db.sheets['main'] = SubjectsData(pandas.DataFrame({
        'subj': ['S1', 'S2'],
        'session': [1, 1],
        'age':[1,2]
    }))

    # Create a new MSHDB instance with subjects
    new_subjects_db = MSHDB(file_schema='test_mshdb_schema.json')
    new_subjects_db.sheets['main'] = SubjectsData(pandas.DataFrame({
        'subj': ['S2', 'S4'],
        'session': [1, 1],
        'age':[20,4]
    }))

    # Add new subjects to the empty database
    updated_db:MSHDB = empty_db.add_new_subjects(new_subjects_db, can_update=True)

    # Assert that the updated database contains the new subjects
    assert updated_db.sheets['main'].df.shape[0] == 3
    assert updated_db.sheets['main'].df['subj'].tolist() == ['S1', 'S2', 'S4']
    assert updated_db.sheets['main'].df['age'].tolist() == [1,20,4]


test_add_new_subjects_to_empty_db()
