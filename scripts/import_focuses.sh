#!/bin/bash
TARGET="focuses"
OUTPUT_TABLE=$firesoutputtable
# copy new data to final focuses table
INSERT="INSERT INTO public.$OUTPUT_TABLE(geom, datahora, satelite, pais, estado, municipio, diasemchuva, precipitacao, riscofogo, latitude, longitude, frp, data) "
INSERT=$INSERT"SELECT geometries as geom, data_hora_::text as datahora, satelite, pais, estado, municipio, numero_dia as diasemchuva, precipitac as precipitacao, risco_fogo as riscofogo, latitude, longitude, frp, data_hora_::date as data FROM $TARGET "
# used to update the biome information into output table
UPDATE="UPDATE public.$OUTPUT_TABLE	SET bioma=b.bioma "
UPDATE="${UPDATE} FROM public.lm_bioma_250 as b "
UPDATE="${UPDATE} WHERE public.focos_aqua_referencia.bioma IS NULL "
UPDATE="${UPDATE} AND ST_CoveredBy(public.$OUTPUT_TABLE.geom, b.geom)"
# drop the intermediary table
DROP_DAILY_TABLE="DROP TABLE IF EXISTS $TARGET"
# exec process
. ./import_data.sh