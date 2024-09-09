"""
Update Previous

Copyright 2024 TerraBrasilis

Usage:
    Used to update the previous uncompleted imported data.
"""
import sys
sys.path.insert(0,'../scripts/python')
from python.data_checker import DataChecker
from python.download_data import DownloadData
from python.import_data import ImportData

class UpdateDatabase:
    """
        The Update Previous is used to perform the update of previously imported data to complete the series.
    """

    def __init__(self):
        self.dc=DataChecker()
        self.down=DownloadData()
        self.import_data=ImportData()

    def updateCurrentData(self):
        # download data
        num_rows, base_file_name, total_files, default_crs=self.down.get()
        if num_rows>0 and total_files>=1:
            # import to database
            file_number=1
            while file_number<total_files:
                file_name="{0}_part{1}.zip".format(base_file_name, file_number)
                self.import_data.importFile(file_name=file_name, default_crs=default_crs)
                file_number+=1

    def updateLastData(self):

        update_data=self.dc.check()

        for aData in update_data:
            self.down.setPeriod(start_date=aData["start_date"],end_date=aData["end_date"])
            num_rows, base_file_name, total_files, default_crs=self.down.get()
            if num_rows==aData["num_rows"]:
                # import to database
                file_number=1
                while file_number<total_files:
                    file_name="{0}_part{1}.zip".format(base_file_name, file_number)
                    self.import_data.importFile(file_name=file_name, default_crs=default_crs, reloaded_id=aData["id"])
                    file_number+=1

# end class

aTask = UpdateDatabase()
aTask.updateCurrentData()
aTask.updateLastData()