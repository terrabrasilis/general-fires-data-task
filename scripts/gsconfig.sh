#!/bin/bash
if [[ -f "$DATA_DIR/config/gsconfig" ]];
then
  source "$DATA_DIR/config/gsconfig"
  export FOCUSES_USER=$FOCUSES_USER
  export FOCUSES_PASS=$FOCUSES_PASS

  if [[ -v GEOSERVER_BASE_URL && -v GEOSERVER_BASE_PATH ]]; then
    export GEOSERVER_BASE_URL=$GEOSERVER_BASE_URL
    export GEOSERVER_BASE_PATH=$GEOSERVER_BASE_PATH
  fi

else
  echo "Missing GeoServer config file."
  echo "Proceed without username and password."
fi