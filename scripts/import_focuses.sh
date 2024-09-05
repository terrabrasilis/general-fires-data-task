#!/bin/bash
TARGET="focuses"
OUTPUT_TABLE=$firesoutputtable

# drop the intermediary table
DROP_TMP_TABLE="DROP TABLE IF EXISTS ${TARGET};"

# copy new data to final focuses table
INSERT="INSERT INTO public.$OUTPUT_TABLE(uuid, data, satelite, pais, estado, municipio, bioma_old, latitude, longitude, geom) "
INSERT=$INSERT"SELECT foco_id, datahora, satelite, pais, estado, municipio, bioma, latitude, longitude, geom FROM $TARGET ON CONFLICT DO NOTHING;"

# used to update the biome information into output table
UPDATE=""
UPDATE="${UPDATE} WITH focos AS ( "
UPDATE="${UPDATE} 	SELECT f.fid, b.bioma FROM public.lm_bioma_250 as b, public.$OUTPUT_TABLE as f "
UPDATE="${UPDATE} 	WHERE f.bioma IS NULL AND ST_Intersects(f.geom, b.geom) "
UPDATE="${UPDATE} ) "
UPDATE="${UPDATE} UPDATE public.$OUTPUT_TABLE SET bioma=f.bioma "
UPDATE="${UPDATE} FROM focos as f "
UPDATE="${UPDATE} WHERE public.$OUTPUT_TABLE.fid=f.fid;"

# exec process
. ./import_data.sh