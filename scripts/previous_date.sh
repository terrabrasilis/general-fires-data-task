#!/bin/bash
SQL="SELECT MAX(end_date) FROM public.acquisition_data_control"
# obtain the previous date from the last import process, if any
PREV_DATE=($($PG_BIN/psql $PG_CON -t -c "$SQL"))
# export to read inside download-data.py python script
# name of var should change, i do not why!
# if keep equal PREV_DATE, getenv do not work inside python
PREVIOUS_DATE=$PREV_DATE
export PREVIOUS_DATE
