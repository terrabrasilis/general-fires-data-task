"""
Check data via WFS

Copyright 2024 TerraBrasilis

Usage:
    Used to find the previous uncompleted imported data.
"""
import os
from python.psqldb import PsqlDB
from python.wfs import WFS

"""
    The Data Checker is used to verify that previously imported data is complete.
"""
class DataChecker:

    def __init__(self, number_of_days=10):
        """
        Constructor.

        Some configuration parameters are expected.
            - number_of_days, the number of previous days to check.
        """
        self.NUMBER_OF_DAYS=number_of_days

        db_conf_file = os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data/config/'
        self.db = PsqlDB(db_conf_file,'db.cfg','raw_fires_data')
        self.db.connect()

        gs_conf_file = os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data/config/'
        self.wfs = WFS(gs_conf_file,'geoserver.cfg','geoserver')

    def __getRegistryFromLog(self):
        """
        Get from the database log the period and number of rows imported for a specified number of days back.
        """
        check_data="SELECT id, start_date, end_date, num_rows FROM public.acquisition_data_control "
        check_data=f"{check_data} WHERE NOT reloaded "
        check_data=f"{check_data} ORDER BY processed_at DESC LIMIT {self.NUMBER_OF_DAYS};"
        
        log=self.db.fetchData(query=check_data)
        return log

    def __getRegistryFromSource(self, start_date, end_date):
        """
        Get the number of available registers from the official data source using the previous period of imported data as a filter.
        """
        self.wfs.setPeriod(start_date=start_date,end_date=end_date)
        return self.wfs.countMax()
    
    def check(self):
        """
        Compare the number of records available with the previously downloaded data.
        
        Return the list of start_date and end_date that need to be reloaded.
        Each item has the following information:
            {
                'start_date':start_date,
                'end_date':end_date,
                'num_rows':official_num_rows
            }
        """
        
        reload=[]

        rows=self.__getRegistryFromLog()
        for row in rows:
            # prepare the parameters to request the count number of rows for a specific period over the WFS
            id=row[0]
            start_date=row[1]
            end_date=row[2]
            imported_num_rows=row[3]
            # get official number of rows
            official_num_rows=self.__getRegistryFromSource(start_date=start_date,end_date=end_date)

            if imported_num_rows<official_num_rows:
                print("we need reimport data to this period")
                row={
                    'id':id,
                    'start_date':start_date,
                    'end_date':end_date,
                    'num_rows':official_num_rows
                }
                reload.append(row)
        
        return reload