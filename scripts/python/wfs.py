"""
WFS client

Copyright 2024 TerraBrasilis

Usage:
  Basic WFS client functions to get count and download data
"""

import requests, os, io
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree as xmlTree
from common_config import ConfigLoader

"""
    WFS client with basic functions.

    Important note: If the range used to filter is very wide, the number of resources
    returned may be greater than the maximum limit allowed by the server.
    In this case, this version has been prepared for pagination and the shapefile is
    downloaded in parts.
"""
class WFS:

    """
    Constructor
        To provide the configuration parameters to WFS service requests, are two alternatives.
        You can mix over this options.
        
        From environment variables file:

            - geoserver_base_url, the target server URL.
            - geoserver_base_path, the path to the WFS service.
            - workspace, the workspace name where the layer is.
            - layer, the layer name to request data via WFS.
            - sort_attribute, the column name used to order by data on pagination dataset.
            - date_attribute, the column name used to filter data by period.
            - start_date, the date as start period.
            - end_date, the date as end period.
            - output_dir, to define the location where the output files will be stored.
            - user, the user name used to authentication on the server.
            - password, the password value used to authentication on the server.

        From configuration file:
            - config_path = 'the/path/to/config/file/'
            - filename = 'geoserver.cfg' (see the README file for format and var names)
            - section = 'session_name_to_wfs_config'
        
        To support the secrets from swarm mode, you can set the user and password to Geoserver:
            - GEOSERVER_USER_FILE, user, the location of secret file on memory in runtime;
            - GEOSERVER_PASS_FILE, password, the location of secret file on memory in runtime;
    """
    def __init__(self, config_path, filename='geoserver.cfg', section='geoserver'):
        # read WFS parameters
        try:
            conf = ConfigLoader(config_path, filename, section)
            self.params = conf.get()
            
            # from the env file
            self.GEOSERVER_BASE_URL=self.params["geoserver_base_url"] if self.params["geoserver_base_url"] else os.getenv("GEOSERVER_BASE_URL", "https://terrabrasilis.dpi.inpe.br")
            self.GEOSERVER_BASE_PATH=self.params["geoserver_base_path"] if self.params["geoserver_base_path"] else os.getenv("GEOSERVER_BASE_PATH", "queimadas/geoserver")
            self.WORKSPACE_NAME=self.params["workspace"] if self.params["workspace"] else os.getenv("WORKSPACE_NAME", "terrabrasilis")
            self.LAYER_NAME=self.params["layer"] if self.params["layer"] else os.getenv("LAYER_NAME", "focos_br_ref_2016")
            self.CQL_DATE_ATTRIBUTE=self.params["date_attribute"] if self.params["date_attribute"] else os.getenv("DATE_ATTRIBUTE", "datahora")
            self.SORT_ATTRIBUTE=self.params["sort_attribute"] if self.params["sort_attribute"] else os.getenv("SORT_ATTRIBUTE", "fid")
            self.GEOSERVER_USER=self.params["user"] if self.params["user"] else os.getenv("GEOSERVER_USER", "admin")
            self.GEOSERVER_PASS=self.params["password"] if self.params["password"] else os.getenv("GEOSERVER_PASS", "geoserver")
            
            # get user and password for geoserver from secrets
            self.GEOSERVER_USER = os.getenv("GEOSERVER_USER_FILE", self.GEOSERVER_USER)
            if os.path.exists(self.GEOSERVER_USER):
                self.GEOSERVER_USER = open(self.GEOSERVER_USER, 'r').read()
            self.GEOSERVER_PASS = os.getenv("GEOSERVER_PASS_FILE", self.GEOSERVER_PASS)
            if os.path.exists(self.GEOSERVER_PASS):
                self.GEOSERVER_PASS = open(self.GEOSERVER_PASS, 'r').read()

        except Exception as configError:
            raise configError

        self.serverLimitByTarget=10000
        self.CQL_START_DATE=None
        self.CQL_END_DATE=None

        self.AUTH=None
        if self.GEOSERVER_USER and self.GEOSERVER_PASS:
            self.AUTH=HTTPBasicAuth(self.GEOSERVER_USER, self.GEOSERVER_PASS)

    def __buildBaseURL(self):

        return "{0}/{1}/{2}/wfs".format(self.GEOSERVER_BASE_URL,self.GEOSERVER_BASE_PATH,self.WORKSPACE_NAME)

    def __buildQueryString(self, OUTPUTFORMAT=None):
        """
        Building the query string to call the WFS service.

        The parameter: OUTPUTFORMAT, the output format for the WFS GetFeature operation described
        in the AllowedValues section in the capabilities document.
        """
        # WFS parameters
        SERVICE="WFS"
        REQUEST="GetFeature"
        VERSION="2.0.0"
        # if OUTPUTFORMAT is changed, check the output file extension within the get method in this class.
        OUTPUTFORMAT=("SHAPE-ZIP" if not OUTPUTFORMAT else OUTPUTFORMAT)
        exceptions="text/xml"
        # define the output projection. We use the layer default projection. (Geography/SIRGAS2000)
        srsName="EPSG:4674"
        # the layer definition
        TYPENAME=self.LAYER_NAME  #{0}:{1}".format(self.WORKSPACE_NAME,self.LAYER_NAME)

        CQL_FILTER="{0} between {1} AND {2}".format(self.CQL_DATE_ATTRIBUTE,self.CQL_START_DATE,self.CQL_END_DATE)

        allLocalParams=locals()
        allLocalParams.pop("self",None)
        PARAMS="&".join("{}={}".format(k,v) for k,v in allLocalParams.items())

        return PARAMS

    def __xmlRequest(self, url):
        root=None
        if self.AUTH:
            response=requests.get(url, auth=self.AUTH)
        else:
            response=requests.get(url)

        if response.ok:
            xmlInMemory = io.BytesIO(response.content)
            tree = xmlTree.parse(xmlInMemory)
            root = tree.getroot()

        return root

    def __getServerLimit(self):
        """
        Read the data download service limit via WFS

        serverLimit: Optional parameter to inform the default limit on GeoServer
        """
        serverLimit=self.serverLimitByTarget
        url="{0}?{1}".format(self.__buildBaseURL(),"service=wfs&version=2.0.0&request=GetCapabilities")

        XML=self.__xmlRequest(url)

        if XML is not None and '{http://www.opengis.net/wfs/2.0}WFS_Capabilities'==XML.tag:
            for p in XML.findall(".//{http://www.opengis.net/ows/1.1}Operation/[@name='GetFeature']"):
                dv=p.find(".//{http://www.opengis.net/ows/1.1}Constraint/[@name='CountDefault']")
                serverLimit=dv.find('.//{http://www.opengis.net/ows/1.1}DefaultValue').text

        return int(serverLimit)

    def __getPageFeature(self, pagination="startIndex=0", pagNumber=1):
        url="{0}?{1}&{2}".format(self.__buildBaseURL(), self.__buildQueryString(), pagination)

        # the extension of output file is ".zip" because the OUTPUTFORMAT is defined as "SHAPE-ZIP"
        output_file="{0}/{1}_part{2}.zip".format(self.DATA_DIR, self.OUTPUT_FILENAME, pagNumber)
        if self.AUTH:
            response=requests.get(url, auth=self.AUTH)
        else:
            response=requests.get(url)

        if response.ok:
            with open(output_file, 'wb') as f:
                f.write(response.content)
        else:
            print("Download fail with HTTP Error: {0}".format(response.status_code))

    def setPeriod(self, start_date, end_date):
        # used to filter data
        self.CQL_START_DATE=start_date
        self.CQL_END_DATE=end_date
        
    def countMax(self):
        """
        Read the number of lines of results expected in the download using the defined filters.
        """
        if self.CQL_START_DATE is None or self.CQL_END_DATE is None:
            raise Exception("Missing period to filter data. Call the setPeriod to do that.")
        
        url="{0}?{1}".format(self.__buildBaseURL(), self.__buildQueryString())
        url="{0}&{1}".format(url,"resultType=hits")
        numberMatched=0
        XML=self.__xmlRequest(url)
        if XML is not None and '{http://www.opengis.net/wfs/2.0}FeatureCollection'==XML.tag:
            numberMatched=XML.find('[@numberMatched]').get('numberMatched')
        else:
            print("Failed to count maximum results for current filter. If the number found is 0, it will exit.")
            print("numberMatched:"+str(numberMatched))

        return int(numberMatched)

    def download(self, output_dir):
        """
        Perform the download and return the number of rows in the data.
        """
        if self.CQL_START_DATE is None or self.CQL_END_DATE is None:
            raise Exception("Missing period to filter data. Call the setPeriod to do that.")

        self.DATA_DIR=output_dir
        
        # create the base directory to store downloaded data
        os.makedirs(self.DATA_DIR, exist_ok=True) # create the output directory if it not exists

        # The output file name (layer_name_start_date_end_date)
        self.OUTPUT_FILENAME="{0}_{1}_{2}".format(self.LAYER_NAME,self.CQL_START_DATE,self.CQL_END_DATE)

        # get server limit and count max number of results
        sl=self.__getServerLimit()
        rr=self.countMax()
        # define the start page number
        pagNumber=1
        # define the start index of data
        startIndex=0
        # define the attribute to sort data
        sortBy=self.SORT_ATTRIBUTE
        # using the server limit to each download
        count=sl
        # pagination iteraction
        while(startIndex<rr):
            paginationParams="count={0}&sortBy={1}&startIndex={2}".format(count,sortBy,startIndex)
            self.__getPageFeature(paginationParams,pagNumber)
            startIndex=startIndex+count
            pagNumber=pagNumber+1
        
        return rr

# end of class
