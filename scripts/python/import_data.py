"""
Update Previous

Copyright 2024 TerraBrasilis

Usage:
    Used to update the previous uncompleted imported data.
"""
import os
import zipfile
import geopandas as gpd
from sqlalchemy import URL,create_engine
from pathlib import Path
from scripts.python.psqldb import PsqlDB


class ImportData():
    """
    Read data from shapefile and load into database.

    """

    def __init__(self, data_dir, tmp_output_table="focuses", output_table="focos_aqua_referencia"):

        self.input_dir=data_dir
        self.tmp_output_table=tmp_output_table
        self.output_table=output_table

        db_conf_file = os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data/config/'
        self.db = PsqlDB(db_conf_file,'db.cfg','raw_fires_data')
        self.db.connect()

        self._dbparams = self.db.getDBParameters()
        dburl=URL.create(drivername=self._dbparams["drivername"],host=self._dbparams["host"],database=self._dbparams["database"],
                         port=self._dbparams["port"],username=self._dbparams["username"],password=self._dbparams["password"])
        self._engine = create_engine(dburl)


    def __load_input_data(self, file_name):
        """
        Used to unpack the shapefile from a ZIP file.

        file_name, is the name of ZIP file, with extension, where the shapefile is.
        """
        try:
            output_dir=f"{self.input_dir}{os.sep}tmp/"
            # create the output directory, if it not exists, to unpack zip
            os.makedirs(output_dir, exist_ok=True)
            
            with zipfile.ZipFile(f"{self.input_dir}{os.sep}{file_name}","r") as zip_ref:
                zip_ref.extractall(output_dir)
            
            file_name=Path(f"{output_dir}{os.sep}{file_name}").stem
            if os.path.isfile(f"{output_dir}{os.sep}{file_name}.shp"):
                self._input_data=gpd.read_file(f"{output_dir}{os.sep}{file_name}.shp")
        except Exception as e:
            print('Error on read data from file')
            print(e.__str__())
            raise e

    def __import_into_database(self):

        try:
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
            insert=f"{insert} municipio, bioma_old, latitude, longitude, geom) "
            insert=f"{insert} SELECT foco_id, datahora, satelite, pais, estado, "
            insert=f"{insert} municipio, bioma, latitude, longitude, geom FROM public.{self.tmp_output_table} "
            insert=f"{insert} ON CONFLICT DO NOTHING;"

            self.db.execQuery(insert)
        except Exception as e:
            print('Error on write data to final table')
            print(e.__str__())
            raise e


    def __update_biome(self):
        """
        used to update the biome information into output table
        """
        try:
            update=f"         WITH focos AS ( "
            update=f"{update} 	SELECT f.fid, b.bioma FROM public.lm_bioma_250 as b, public.{self.output_table} as f "
            update=f"{update} 	WHERE f.bioma IS NULL AND ST_Intersects(f.geom, b.geom) "
            update=f"{update} ) "
            update=f"{update} UPDATE public.{self.output_table} SET bioma=f.bioma "
            update=f"{update} FROM focos as f "
            update=f"{update} WHERE public.{self.output_table}.fid=f.fid;"

            self.db.execQuery(update)
        except Exception as e:
            print('Error on update biome')
            print(e.__str__())
            raise e

    def __set_acquisition_data_control(self, start_date, end_date, num_rows):

        try:
            insert_info="INSERT INTO public.acquisition_data_control(start_date, end_date, num_rows, origin_data) "
            insert_info=f"{insert_info} VALUES ('{start_date}', '{end_date}', {num_rows},'{self.tmp_output_table}');"

            self.db.execQuery(insert_info)
        except Exception as e:
            print('Error on write acquisition data control')
            print(e.__str__())
            raise e
    
    def exec(self):
        try:
            # get from WFS service
            self.__load_input_data()
            # import into temporary table
            self.__import_into_database()

            # open transaction
            self.__copy_to_final_table()
            self.__update_biome()
            self.__set_acquisition_data_control()
            self.db.commit()
            self.db.close()
        except Exception as e:
            print('Error on perform the import data from shapefile to database')
            print(e.__str__())
            raise e