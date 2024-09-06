## Preparation of fire focuses data

***Used in AMS, but not limited to.**

Automation or semi-automation to read data of fire focuses from geoservice of Queimadas portal and import into database in TerraBrasilis infrastructure.

The expected periodicity is daily for the acquisition of new data.

Taking all the data of active fires from BR and executing an UPDATE routine to change the name of the old biome to the new biome.

## Configurations

There are a few possibilities to pass settings to scripts.

The configuration files and a control table to prepare the execution environment, as follows:

 - config/gsconfig (settings for GeoServer - Queimadas)
 - config/geoserver.cfg (settings for GeoServer - Queimadas, using by Python scripts)
 - config/pgconfig (database settings to import and process data)
 - config/db.cfg (database settings to import and process data, using by Python scripts)


### Runtime Settings

Some data such as GeoServer URL must be configured using environment variables in the docker command, in the docker stack definition or in the gsconfig file, in the session below.

 > Fragment example of docker stack with the expected env vars
```
    environment:
        GEOSERVER_BASE_URL: https://terrabrasilis.dpi.inpe.br
        GEOSERVER_BASE_PATH: queimadas/geoserver
```

#### Configuration files details

 > Content of gsconfig file
```txt
GEOSERVER_BASE_URL="https://terrabrasilis.dpi.inpe.br"
GEOSERVER_BASE_PATH="queimadas/geoserver"
WORKSPACE_NAME="terrabrasilis"
LAYER_NAME="focos"
DATE_ATTRIBUTE="datahora"
SORT_ATTRIBUTE="fid"
GEOSERVER_USER="user to login on geoserver of Queimadas"
GEOSERVER_PASS="password to login on geoserver of Queimadas"
```
*GEOSERVER_BASE_URL and GEOSERVER_BASE_PATH are optional here. It can be provided as env var in the start command, discussed in the "Runtime Settings" section.

 > Content of geoserver.cfg file
```txt
[geoserver]
geoserver_base_url: https://terrabrasilis.dpi.inpe.br
geoserver_base_path: queimadas/geoserver
workspace: terrabrasilis
layer: focos
sort_attribute: fid
date_attribute: datahora
user: aGeoserverUser
password: aGeoserverPassword
```

 > Content of pgconfig file
```txt
user="postgres"
host="localhost"
port="5432"
database="raw_fire_data"
password="postgres"
firesoutputtable="focos_aqua_referencia"
```

 > Content of db.cfg file
```txt
[raw_fires_data]
host: localhost
port: 5432
user: postgres
password: postgres
dbname: raw_fires_data
```

### Database requirements

The precondition to start the process is the existence of the tables into the Postgis database:
 - public.focos_aqua_referencia (a output table to store the imported data)
 - public.lm_bioma_250 (a biome table used to update the biome column in the imported data)
 - public.acquisition_data_control (a control table for imported data)

 > Table with the biome borders
```sql
CREATE TABLE IF NOT EXISTS public.lm_bioma_250
(
    id serial,
    geom geometry(MultiPolygon,4674),
    bioma character varying(254) COLLATE pg_catalog."default",
    cd_bioma integer,
    area_km double precision,
    CONSTRAINT lm_bioma_250_pkey PRIMARY KEY (id)
);
```

 > Table to control the data acquisition process
```sql
CREATE TABLE public.acquisition_data_control
(
    id serial,
    start_date date,
    end_date date,
    num_rows integer,
    origin_data character varying(80) COLLATE pg_catalog."default",
    processed_at date DEFAULT (now())::date,
    CONSTRAINT acquisition_data_control_id_pk PRIMARY KEY (id)
);
```

 > Table to import the data
```sql
CREATE TABLE IF NOT EXISTS public.focos_aqua_referencia
(
    fid serial,
    uuid character varying(254) COLLATE pg_catalog."default",
    data date,
    satelite character varying COLLATE pg_catalog."default",
    pais character varying COLLATE pg_catalog."default",
    estado character varying COLLATE pg_catalog."default",
    municipio character varying COLLATE pg_catalog."default",
    bioma character varying COLLATE pg_catalog."default",
    bioma_old character varying COLLATE pg_catalog."default",
    latitude double precision,
    longitude double precision,
    geom geometry(Point,4674),
    imported_at date NOT NULL DEFAULT (now())::date,
    CONSTRAINT focos_aqua_referencia_pkey PRIMARY KEY (fid),
    CONSTRAINT focos_aqua_referencia_uuid_unique UNIQUE (uuid)
);
```