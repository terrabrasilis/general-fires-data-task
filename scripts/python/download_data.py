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
from scripts.python.wfs import WFS

"""
  Used to perform the download of shapefiles using WFS service.
"""
class DownloadWFS:

  def __init__(self, previous_date=None, output_dir=None):
    """
    Constructor

    Define configurations on instantiate.

      - previous_date, optional - used to generate a period in the past, starting on the day after this date and
        ending on the day yesterday of the current date. Default is the yesterday of the current date.

      - output_dir, optional - the location to write the downloaded data files.
        Default is the data directory at ../../data/
    """
    # Data directory for writing downloaded data
    self.DIR=output_dir if output_dir else os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data/'
    self.DATA_DIR=os.getenv("DATA_DIR", f"{self.DIR}")
    # any past date used as the start date of the period filter.
    self.PREVIOUS_DATE=os.getenv("PREVIOUS_DATE", f"{previous_date}")

    gs_conf_file = os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data/config/'
    self.wfs = WFS(gs_conf_file,'geoserver.cfg','geoserver')

    self.START_DATE,self.END_DATE=None

  def __getPeriod(self):
    """
    The start date and end date are automatically detected using the machine's calendar
    and represent the first and last day of one perid.
    Used as period filter on download or count data.
    """
    prev_date=yesterday_date=(datetime.today() - timedelta(days=1)).date()

    if self.PREVIOUS_DATE:
      prev_date=datetime.strptime(str(self.PREVIOUS_DATE),'%Y-%m-%d')
      prev_date=(prev_date + timedelta(days=1)).date()

    if prev_date<yesterday_date:
      dt0="{0} 00:00:00".format(prev_date.strftime('%Y-%m-%d'))
      dt1="{0} 23:59:59".format(yesterday_date.strftime('%Y-%m-%d'))
    else:
      dt0="{0} 00:00:00".format(yesterday_date.strftime('%Y-%m-%d'))
      dt1="{0} 23:59:59".format(yesterday_date.strftime('%Y-%m-%d'))

    start_date=datetime.strptime(str(dt0),'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S')
    end_date=datetime.strptime(str(dt1),'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S')

    return start_date, end_date
  
  def setPeriod(self, start_date, end_date):
    # used to filter data
    self.START_DATE=start_date
    self.END_DATE=end_date

  def getFocuses(self):
    
    if self.START_DATE is None or self.END_DATE is None:
      # define start and end date as yesterday or based on PREVIOUS_DATE, if provided
      self.START_DATE,self.END_DATE=self.__getPeriod()

    # download Focuses of fire
    self.wfs.setPeriod(start_date=self.START_DATE,end_date=self.END_DATE)
    rows=self.wfs.download(output_dir=self.DATA_DIR)
    return rows

  def get(self):
    try:
      return self.getFocuses()
    except Exception as error:
      print("There was an error when trying to download data.")
      print(error)

# end of class
