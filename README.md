## Preparation of fire focuses data

***Used in AMS, but not limited to.**

Automation or semi-automation to read data of fire focuses from geoservice of Queimadas portal and import into database in TerraBrasilis infrastructur.

The expected periodicity is daily for the acquisition of new data.

Taking all the data of active fires from BR and executing an UPDATE routine to change the name of the old biome to the new biome.

## Configurations

There are three configuration files and a control table to prepare the execution environment, as follows:

 - config/gsconfig (user and password settings for GeoServer - Queimadas)
 - config/pgconfig (database settings to import and process data)
 - public.acquisition_data_control (a control table for imported data)

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
FOCUSES_USER="user to login on geoserver of Queimadas."
FOCUSES_PASS="password to login on geoserver of Queimadas."
GEOSERVER_BASE_URL="https://terrabrasilis.dpi.inpe.br"
GEOSERVER_BASE_PATH="queimadas/geoserver"
```
*GEOSERVER_BASE_URL and GEOSERVER_BASE_PATH are optional here. It can be provided as env var in the start command, discussed in the "Runtime Settings" section.


 > Content of pgconfig file
```txt
user="postgres"
host="localhost"
port="5432"
database="raw_fire_data"
password="postgres"
firesoutputtable="focos_aqua_referencia"
```

### Database requirements

 > Table to control the data acquisition process
```sql
CREATE TABLE public.acquisition_data_control
(
    id integer NOT NULL DEFAULT nextval('acquisition_data_control_id_seq'::regclass),
    start_date date,
    end_date date,
    num_rows integer,
    origin_data character varying(80) COLLATE pg_catalog."default",
    created_at date DEFAULT (now())::date,
    CONSTRAINT acquisition_data_control_id_pk PRIMARY KEY (id)
);
```