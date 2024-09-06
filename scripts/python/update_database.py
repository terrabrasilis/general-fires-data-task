"""
Update Previous

Copyright 2024 TerraBrasilis

Usage:
    Used to update the previous uncompleted imported data.
"""
from scripts.python.data_checker import DataChecker
from scripts.python.download_data import DownloadWFS
from scripts.python.import_data import ImportData

class UpdatePrevious:
    """
        The Update Previous is used to perform the update of previously imported data to complete the series.
    """

    def __init__(self):
        self.dc=DataChecker(number_of_days=5)
        self.down=DownloadWFS()
        self.import_data=ImportData()

    def getNewData(self):
        # download data
        num_rows=self.down.get()
        if num_rows>0:
            # import to database
            pass

    def updateLastData(self):

        update_data=self.dc.check()

        for aData in update_data:
            print(aData)
            self.down.setPeriod(start_date=aData["start_date"],end_date=aData["end_date"])
            num_rows=self.down.get()
            if num_rows==aData["num_rows"]:
                # import to database
                pass