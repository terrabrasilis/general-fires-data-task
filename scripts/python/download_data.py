"""
Download via WFS
Download Shapefile Focuses

Copyright 2024 TerraBrasilis

Usage:
  Used to perform the download of shapefiles using WFS service.

This is based on the DETER data download example provided in the following link.
https://gist.github.com/andre-carvalho/45eaf4378fbf91d0514a995a80c69d98
"""
import os
from datetime import datetime, timedelta
from python.psqldb import PsqlDB
from python.wfs import WFS

"""
  Used to perform the download of shapefiles using WFS service.
"""
class DownloadData:

  def __init__(self, previous_date=None, output_dir=None):
    """
    Constructor

    Define configurations on instantiate.

        The default is to read the previous date from the database.
        If there is no value from the database, the yesterday of the current date is the default.

      - output_dir, optional - the location to write the downloaded data files.
        Default is the data directory at ../../data/
    """
    # Data directory for writing downloaded data
    self.DIR=output_dir if output_dir else os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data/'
    self.DATA_DIR=os.getenv("DATA_DIR", f"{self.DIR}")

    gs_conf_file = os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data/config/'
    self.wfs = WFS(gs_conf_file,'geoserver.cfg','geoserver')

    db_conf_file = os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data/config/'
    self.db = PsqlDB(db_conf_file,'db.cfg','raw_fires_data')

    self.START_DATE=self.END_DATE=self.PREVIOUS_DATE=None
    self.YESTERDAY_DATE=(datetime.today() - timedelta(days=1)).date()

  def __getPeriod(self, previous_date=None):
    """
    The start date and end date are automatically detected using the machine's calendar
    and represent the first and last day of one perid.
    Used as period filter on download or count data.

    - previous_date, optional - used to generate a period in the past, starting on the day
      after the previous_date date and ending on the day yesterday of the current date.
    """
    prev_date=self.YESTERDAY_DATE

    if previous_date is not None:
      prev_date=datetime.strptime(str(previous_date),'%Y-%m-%d')
      prev_date=(prev_date + timedelta(days=1)).date()

    start_date=f"{prev_date.strftime('%Y-%m-%d')}"
    end_date=f"{self.YESTERDAY_DATE.strftime('%Y-%m-%d')}"

    return start_date, end_date
  
  def setPeriod(self, start_date, end_date):
    # used to filter data
    self.START_DATE=start_date
    self.END_DATE=end_date

  def getPreviousDateFromDB(self):
    pdate=None
    self.db.connect()
    prev_date="SELECT MAX(end_date) FROM public.acquisition_data_control;"
    row=self.db.fetchData(query=prev_date)
    if len(row[0])==1:
      pdate=datetime.strptime(str(row[0][0]),'%Y-%m-%d').date()

    return pdate


  def getFocuses(self):
    # use to abort if download is not needed
    escape=False

    if self.START_DATE is None or self.END_DATE is None:
      # try read from database
      previous_date=self.getPreviousDateFromDB()
      if previous_date is None:
        # define start and end date as yesterday
        self.START_DATE,self.END_DATE=self.__getPeriod()
      elif previous_date < self.YESTERDAY_DATE:
        # if the previous date is older than yesterday, define start and end date based on previous_date
        self.START_DATE,self.END_DATE=self.__getPeriod(previous_date=previous_date)
      elif previous_date == self.YESTERDAY_DATE:
        # abort
        escape=True
        rows=pagNumber=0
        file_name=default_crs=None

    if not escape:
      # download Focuses of fire using start and end date from call
      default_crs=self.wfs.getDefaultEPSG()
      self.wfs.setPeriod(start_date=self.START_DATE,end_date=self.END_DATE)
      rows, file_name, pagNumber=self.wfs.download(output_dir=self.DATA_DIR)

    return rows, file_name, pagNumber, default_crs

  def get(self):
    try:
      return self.getFocuses()
    except Exception as error:
      print("There was an error when trying to download data.")
      print(error)

# end of class
