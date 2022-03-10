#!/bin/bash
# to debug in localhost
SCRIPT_DIR=`pwd`
SHARED_DIR=$SCRIPT_DIR"/../data"
# to store run log
DATE_LOG=$(date +"%Y-%m-%d_%H:%M:%S")
# The data work directory.
DATA_DIR=$SHARED_DIR
export DATA_DIR

# go to the scripts directory
cd $SCRIPT_DIR
# load geoserver user and password from config file in config/gsconfig
. ./gsconfig.sh
# load postgres parameters from config file in config/pgconfig
. ./dbconf.sh
# get previous date
. ./previous_date.sh
# get focuses for previous day
python3 download-data.py

. ./import_focuses.sh >> "$DATA_DIR/import_focuses_$DATE_LOG.log" 2>&1