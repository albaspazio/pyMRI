import os
import json

from data.SubjectsData import SubjectsData


class VolBrainImporter:
    """
    This class imports the Ceres dataset.

    Parameters
    ----------
    schema : str
        path to json containing valid columns
    inputfolder : str
        The path to the folder containing the Ceres CSV files.
    outfile : str or None, optional
        The path to the output CSV file. If None, the data will not be saved.

    Attributes
    ----------
    inputfolder : str
        The path to the folder containing the Ceres CSV files.
    outfile : str or None
        The path to the output CSV file. If None, the data will not be saved.
    outcolnames : list of str
        The list of output column names.
    subs_data : SubjectsData
        The SubjectsData object containing the imported data.

    Methods
    -------
    parseFolder(self, valid_columns=None)
        Parse the input folder and return a SubjectsData object containing the data.
    """

    def __init__(self, schema_file:str, inputfolder:str, outfile=None, out_short:bool=True):
        """
        Initialize the CeresImporter class.

        Parameters
        ----------
        inputfolder : str
            The path to the folder containing the Ceres CSV files.
        outfile : str or None, optional
            The path to the output CSV file. If None, the data will not be saved.
        outcolnames : list of str, optional
            The list of output column names. If None, the default column names will be used.
        """
        self.inputfolder    = inputfolder
        self.outfile        = outfile

        with open(schema_file) as json_file:
            self.schema = json.load(json_file)

        if out_short is True:
            self.valid_columns          = self.schema["valid_columns_short"]
            self.out_valid_columns      = self.schema["out_valid_columns_short"]
        else:
            self.valid_columns          = self.schema["valid_columns"]
            self.out_valid_columns      = self.schema["out_valid_columns"]

        self.subs_data = self.parseFolder(self.valid_columns)

        if outfile is not None:
            if isinstance(outfile, str):
                self.subs_data.save_data(outfile, outcolnames=self.out_valid_columns)
            else:
                raise Exception("Error in CeresImporter: given outfile is not a string")

    def parseFolder(self, valid_columns=None) -> SubjectsData:
        """
        Parse the input folder and return a SubjectsData object containing the data.

        Parameters
        ----------
        valid_columns : list of str, optional
            A list of column names that are valid for the Ceres dataset. If None, the default list of valid columns will be used.

        Returns
        -------
        SubjectsData
            A SubjectsData object containing the imported data.
        """
        subjs_data = SubjectsData()
        subjs = []
        for f in os.listdir(self.inputfolder):
            if f.endswith(".csv"):
                full_name = os.path.join(self.inputfolder, f)
                subj_name = f.split("-")[0]

                subj_data                   = SubjectsData(data=full_name, validcols=valid_columns, delimiter=";", check_data=False)  # automatically rename Patient_ID -> subj
                subj_data.df                = subj_data.df.rename(columns={self.valid_columns[0]: self.out_valid_columns[0]})
                subj_data.df.at[0, "subj"]  = subj_name
                subj_data.df.insert(1, "session", [0], True)
                subjs.append(subj_data)

        subjs_data.add_sd(subjs)

        return subjs_data
