#!/bin/bash
TARGET="focuses"
OUTPUT_TABLE=$firesoutputtable

# copy new data to final focuses table
INSERT="INSERT INTO public.$OUTPUT_TABLE(geom, datahora, satelite, pais, estado, municipio, diasemchuva, precipitacao, riscofogo, latitude, longitude, frp, data) "
INSERT=$INSERT"SELECT geometries as geom, data_hora_::text as datahora, satelite, pais, estado, municipio, numero_dia as diasemchuva, precipitac as precipitacao, "
INSERT=$INSERT" risco_fogo as riscofogo, latitude, longitude, frp, data_hora_::date as data FROM $TARGET "

# drop the intermediary table
DROP_TMP_TABLE="DROP TABLE IF EXISTS ${TARGET};"

# used to update the biome information into output table
UPDATE=""
UPDATE="${UPDATE} WITH focos AS ( "
UPDATE="${UPDATE} 	SELECT f.id, b.bioma FROM public.lm_bioma_250 as b, public.$OUTPUT_TABLE as f "
UPDATE="${UPDATE} 	WHERE f.bioma IS NULL AND ST_Intersects(f.geom, b.geom) "
UPDATE="${UPDATE} ) "
UPDATE="${UPDATE} UPDATE public.$OUTPUT_TABLE SET bioma=f.bioma "
UPDATE="${UPDATE} FROM focos as f "
UPDATE="${UPDATE} WHERE public.$OUTPUT_TABLE.id=f.id;"

# exec process
. ./import_data.sh