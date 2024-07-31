The database management in pymri is based on the following classes:

SubjectsData

BayesDB
MSHB
Sheets

The following importers:

BayesImporter
LimeAutoImporter

SubjectSD



A multisheet excel file is represented by a MSHDB instance. 
MSHDB contain an instance of Sheets. 
Sheets is a dict and contains one item for each DB sheet.
these items are instances of SubjectsData

MSHDB.sheets =  {   main: SubjectsData,
                    SA: SubjectsData,
                    CLINIC: SubjectsData,
                    ....
                    ....
                }

SubjectsData is a class active as super-wrapper of a pandas DataFrame