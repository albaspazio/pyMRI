import gspread
from df2gspread import df2gspread as d2g

from datetime import date, datetime
from oauth2client.service_account import ServiceAccountCredentials


class GDriveSheet:
    def __init__(self, ss_id:str, ifolder_id:str, service_account:str, backupfolder_id:str):

        self.ss_id              = ss_id
        self.ifolder_id         = ifolder_id
        self.backupfolder_id    = backupfolder_id

        self.account            = service_account

        scope           = [ 'https://spreadsheets.google.com/feeds',        'https://www.googleapis.com/auth/drive',
                            'https://www.googleapis.com/auth/drive.file',   'https://www.googleapis.com/auth/spreadsheets']
        self.creds      = ServiceAccountCredentials.from_json_keyfile_name(self.account, scope)
        self.client     = gspread.authorize(self.creds)

    def open_ss(self) -> gspread.Spreadsheet:
        gc = gspread.service_account(self.account)
        return gc.open_by_key(self.ss_id) #, self.ifolder_id)

    def get_spreadsheet_id(self, ssname:str, folder_id:str):
        source_id = self.client.list_spreadsheet_files(ssname, folder_id)[0]

    def create_ss(self, name, folder_id, sheets:dict):
        workbook = self.client.create(name, folder_id=folder_id)
        for sh in sheets:
            d2g.upload(sheets[sh].df, workbook.id, sh, credentials=self.creds, df_size = True,
                       col_names=True, row_names=True, start_cell="A1", clean=False)


    def update_file(self, sheets:dict, source:str=None, backuptitle:str=None, backupfolder_id:str=None):

        if source is None:
            source = self.ss_id

        if backuptitle is None:
            backuptitle = "backup"

        if backupfolder_id is None:
            backupfolder_id = self.backupfolder_id

        # source_id = self.client.list_spreadsheet_files(self.ss_id, self.ifolder_id)[0]


        ss_copy = self.client.copy(file_id=source, title=backuptitle, copy_permissions=True, folder_id=backupfolder_id)

        self.client.del_spreadsheet(source)

        for sh in sheets:
            d2g.upload(sheets[sh].df, source, sh, credentials=self.creds, df_size = True,
                       col_names=True, row_names=True, start_cell="A1", clean=False)


