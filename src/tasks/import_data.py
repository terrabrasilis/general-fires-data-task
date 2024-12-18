"""
Update Previous

Copyright 2024 TerraBrasilis

Usage:
    Used to update the previous uncompleted imported data.
"""
import os
import zipfile
import geopandas as gpd
from glob import glob
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from tasks.psqldb import PsqlDB


class ImportData():
    """
    Read data from shapefile and load into database.

    """

    def __init__(self, data_dir=None, tmp_output_table="focuses", output_table="focos_aqua_referencia"):

        # Data directory for reading data
        self.input_dir=data_dir if data_dir else os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data'
        self.DATA_DIR=os.getenv("DATA_DIR", self.input_dir)

        self.tmp_output_table=tmp_output_table
        self.output_table=output_table

        db_conf_file = os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data/config/'
        self.db = PsqlDB(db_conf_file,'db.cfg','raw_fires_data')
        self.db.connect()

        self._dbparams = self.db.getDBParameters()
        dburl=URL.create(drivername=self._dbparams["drivername"],host=self._dbparams["host"],database=self._dbparams["database"],
                         port=self._dbparams["port"],username=self._dbparams["username"],password=self._dbparams["password"])
        self._engine = create_engine(dburl)

        self._input_data=None


    def __load_input_data(self, file_name):
        """
        Used to unpack the shapefile from a ZIP file.

        file_name, is the name of ZIP file, with extension, where the shapefile is.
        """
        try:
            output_dir=f"{self.input_dir}{os.sep}tmp"
            # create the output directory, if it not exists, to unpack zip
            os.makedirs(output_dir, exist_ok=True)
            
            with zipfile.ZipFile(f"{self.input_dir}{os.sep}{file_name}","r") as zip_ref:
                zip_ref.extractall(output_dir)
            
            file_name=glob(f"{output_dir}{os.sep}*.shp")[0]
            if os.path.isfile(file_name):
                self._input_data=gpd.read_file(file_name)
        except Exception as e:
            print('Error on read data from file')
            print(e.__str__())
            raise e

    def __import_into_database(self, default_crs=None):

        try:
            if self._input_data is not None and not self._input_data.empty:
                # force CRS default
                self._input_data.set_crs(crs=default_crs, inplace=True, allow_override=True)
                self._input_data.to_postgis(name=f"{self.tmp_output_table}", schema="public", con=self._engine, if_exists='replace')

        except Exception as e:
            print('Error on write data to database')
            print(e.__str__())
            raise e
        
    def __copy_to_final_table(self):
        """
        copy new data to final focuses table
        """
        try:
            insert=f"INSERT INTO public.{self.output_table}(uuid, data, satelite, pais, estado, "
            insert=f"{insert} municipio, bioma, bioma_old, latitude, longitude, geom) "
            insert=f"{insert} SELECT foco_id, datahora::date, satelite, pais, estado, "
            insert=f"{insert} municipio, bioma_nb, bioma as bioma_old, latitude, longitude, geometry "
            insert=f"{insert} FROM public.{self.tmp_output_table} "
            insert=f"{insert} ON CONFLICT DO NOTHING;"

            self.db.execQuery(insert)
        except Exception as e:
            print('Error on write data to final table')
            print(e.__str__())
            raise e


    def __update_biome(self):
        """
        used to update the biome information on temporary table
        """
        try:
            add_column=f"ALTER TABLE IF EXISTS public.{self.tmp_output_table} ADD COLUMN bioma_nb character varying;"
            self.db.execQuery(add_column)

            update=f" UPDATE public.{self.tmp_output_table} SET bioma_nb=b.bioma "
            update=f"{update} FROM public.lm_bioma_250 as b"
            update=f"{update} WHERE ST_CoveredBy(public.{self.tmp_output_table}.geometry, b.geom);"

            self.db.execQuery(update)
        except Exception as e:
            print('Error on update biome')
            print(e.__str__())
            raise e

    def __set_acquisition_data_control(self, reloaded_id=None):
        """
        Store the control informations into database.

            - reloaded_id, used to identify when a specific period's dataset was reimported.
        """

        try:
            if reloaded_id is not None:
                update_info="UPDATE public.acquisition_data_control SET reloaded=true::boolean"
                update_info=f"{update_info} WHERE id={reloaded_id}"
                self.db.execQuery(update_info)

            insert_info="INSERT INTO public.acquisition_data_control(start_date, end_date, num_rows, reloaded) "
            insert_info=f"{insert_info} SELECT MIN(datahora::date), MAX(datahora::date), count(*), false::boolean "
            insert_info=f"{insert_info} FROM public.{self.tmp_output_table};"
            self.db.execQuery(insert_info)

        except Exception as e:
            print('Error on write acquisition data control')
            print(e.__str__())
            raise e
    
    def importFile(self, file_name, default_crs=None, reloaded_id=None):
        """
        Import a shapefile into the database and update the biome column based on the biome table.

        The biome table must be in the database.

            - file_name, is the path and full name of the desired shapefile.
            - default_crs, is the default CRS of the input file. Used if the file reader fails to determine the CRS.
            - reloaded_id, used to identify when a specific period's dataset was reimported.
        """
        try:
            # load shapefile to memory
            self.__load_input_data(file_name=file_name)
            # import into temporary table
            self.__import_into_database(default_crs=default_crs)

            # open transaction
            self.__update_biome()
            self.__copy_to_final_table()
            self.__set_acquisition_data_control(reloaded_id=reloaded_id)
            self.db.commit()
        except Exception as e:
            print('Error on perform the import data from shapefile to database')
            print(e.__str__())
            raise e