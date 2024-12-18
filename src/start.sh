#!/bin/bash
# to debug in localhost, enable the following line
# SCRIPT_DIR=`pwd`

# The data work directory.
DATA_DIR=$SCRIPT_DIR"/../data"
export DATA_DIR

# go to the scripts directory
cd "${SCRIPT_DIR}/tasks"
# update focuses
python3 update_database.py