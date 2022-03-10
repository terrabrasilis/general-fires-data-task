#!/bin/bash
if [[ -f "$DATA_DIR/config/gsconfig" ]];
then
  source "$DATA_DIR/config/gsconfig"
  export FOCUSES_USER=$FOCUSES_USER
  export FOCUSES_PASS=$FOCUSES_PASS
else
  echo "Missing GeoServer config file."
  echo "Proceed without username and password."
fi