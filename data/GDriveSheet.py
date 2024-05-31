import gspread
from df2gspread import df2gspread as d2g

from datetime import date, datetime
from oauth2client.service_account import ServiceAccountCredentials


class GDriveSheet:
    """
    This class provides methods for interacting with Google Sheets and Google Drive.

    Args:
        ss_id (str): The ID of the Google Sheet to interact with.
        ifolder_id (str): The ID of the folder within Google Drive that contains the Google Sheet.
        service_account (str): The path to the service account credentials file.
        backupfolder_id (str, optional): The ID of the folder within Google Drive to store backups of the Google Sheet. Defaults to None.

    Attributes:
        ss_id (str): The ID of the Google Sheet to interact with.
        ifolder_id (str): The ID of the folder within Google Drive that contains the Google Sheet.
        backupfolder_id (str): The ID of the folder within Google Drive to store backups of the Google Sheet.
        account (str): The path to the service account credentials file.
        creds (google.oauth2.credentials.Credentials): The OAuth2 credentials object.
        client (gspread.client.Client): The Google Sheets API client.
    """

    def __init__(self, ss_id: str, ifolder_id: str, service_account: str, backupfolder_id: str = None):
        self.ss_id = ss_id
        self.ifolder_id = ifolder_id
        self.backupfolder_id = backupfolder_id
        self.account = service_account
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets",
        ]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(
            self.account, scope
        )
        self.client = gspread.authorize(self.creds)

    def open_ss(self) -> gspread.Spreadsheet:
        """Opens the Google Sheet.

        Returns:
            gspread.Spreadsheet: The opened Google Sheet.
        """
        gc = gspread.service_account(self.account)
        return gc.open_by_key(self.ss_id)  # , self.ifolder_id)

    def get_spreadsheet_id(self, ssname: str, folder_id: str) -> str:
        """
        Gets the ID of the Google Sheet with the specified name and folder.

        Args:
            ssname (str): The name of the Google Sheet.
            folder_id (str): The ID of the folder that contains the Google Sheet.

        Returns:
            str: The ID of the Google Sheet.
        """
        source_id = self.client.list_spreadsheet_files(ssname, folder_id)[0]
        return source_id

    def create_ss(self, name, folder_id, sheets: dict) -> gspread.Spreadsheet:
        """
        Creates a new Google Sheet with the specified name, folder, and sheets.

        Args:
            name (str): The name of the Google Sheet.
            folder_id (str): The ID of the folder to create the Google Sheet in.
            sheets (dict): A dictionary of sheets, where the key is the name of the sheet and the value is a pandas.DataFrame.

        Returns:
            gspread.Spreadsheet: The created Google Sheet.
        """
        spreadsheet = self.client.create(name, folder_id=folder_id)
        for sh in sheets:
            d2g.upload(sheets[sh].df, spreadsheet.id, sh, credentials=self.creds, df_size=True,
                       col_names=True, row_names=False, start_cell="A1", clean=False)
        spreadsheet.del_worksheet(spreadsheet.worksheet("Sheet1"))

        return spreadsheet

    def update_file(self, sheets: dict, source: str = None, backuptitle: str = None, backupfolder_id: str = None):
        """
        Updates the Google Sheet with the specified sheets.

        Args:
            sheets (dict): A dictionary of sheets, where the key is the name of the sheet and the value is a pandas.DataFrame.
            source (str, optional): The ID of the Google Sheet to update. If not specified, the ID of the Google Sheet specified in the class constructor is used.
            backuptitle (str, optional): The title of the backup Google Sheet. If not specified, "backup" is used.
            backupfolder_id (str, optional): The ID of the folder to store the backup Google Sheet in. If not specified, the ID of the backup folder specified in the class constructor is used.
        """
        if source is None:
            source = self.ss_id

        if backuptitle is None:
            backuptitle = "backup"

        if backupfolder_id is None:
            backupfolder_id = self.backupfolder_id

        # source_id = self.client.list_spreadsheet_files(self.ss_id, self.ifolder_id)[0]

        if backupfolder_id is not None:
            ss_copy = self.client.copy(file_id=source, title=backuptitle, copy_permissions=True, folder_id=backupfolder_id)

        self.client.del_spreadsheet(source)

        for sh in sheets:
            d2g.upload(sheets[sh].df, source, sh, credentials=self.creds, df_size=True,
                       col_names=True, row_names=True, start_cell="A1", clean=False)


