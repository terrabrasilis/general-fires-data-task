#!/bin/bash
# define de target directory
DATA_TARGET="$DATA_DIR/$TARGET"
# define log file
DATE_LOG=$(date +"%Y-%m-%d_%H:%M:%S")
LOGFILE="$DATA_TARGET/import_$DATE_LOG.log"

# set a default value to numberMatched to skip process if no control file exists.
numberMatched=0
# verify if has new data. If yes, load to env vars the START_DATE, END_DATE and numberMatched
if [[ -f "$DATA_TARGET/acquisition_data_control" ]];
then

  # drop temporary table
  $PG_BIN/psql $PG_CON -t -c "$DROP_TMP_TABLE"

  source "$DATA_TARGET/acquisition_data_control"
  INSERT_INFOS="INSERT INTO public.acquisition_data_control(start_date, end_date, num_rows, origin_data) "
  INSERT_INFOS=$INSERT_INFOS"VALUES ('$START_DATE', '$END_DATE', $numberMatched,'$TARGET');"
  CHECK_DATA="SELECT num_rows FROM public.acquisition_data_control WHERE start_date='$START_DATE' AND end_date='$END_DATE' AND origin_data='$TARGET'"

  # obtain the number of rows from the previous import process, if any
  NUM_ROWS=($($PG_BIN/psql $PG_CON -t -c "$CHECK_DATA"))

  if [[ "$numberMatched" = "$NUM_ROWS" ]];
  then
    echo "The data was imported before" >> $LOGFILE
    echo "If you want to import again, follow these steps:" >> $LOGFILE
    echo " - Verify if your table, $OUTPUT_TABLE, do not have these data;" >> $LOGFILE
    echo " - Verify if the control table, acquisition_data_control, do not have these control data;" >> $LOGFILE
    echo " - Remove the control file, acquisition_data_control;" >> $LOGFILE
    echo "" >> $LOGFILE
    echo "The previous data on the control record are:" >> $LOGFILE
    echo "START_DATE=$START_DATE, END_DATE=$END_DATE, numberMatched=$numberMatched" >> $LOGFILE
  else

    if [ "$(ls -1d $DATA_TARGET/*${START_DATE}*${END_DATE}*.zip 2>/dev/null | wc -l)" -eq 1 ];
    then
      echo "The data will now be imported" >> $LOGFILE

      # to control the import shape mode
      CREATE_TABLE="YES"
      for ZIP_FILE in `ls $DATA_TARGET/*${START_DATE}*${END_DATE}*.zip | awk {'print $1'}`
      do
        FILE_NAME=`basename $ZIP_FILE`

        unzip -o -j "$ZIP_FILE" -d "$DATA_TARGET"

        for SHP_NAME in `ls $DATA_TARGET/*.shp | awk {'print $1'}`
        do
          SHP_NAME=`basename $SHP_NAME`
          SHP_NAME=`echo $SHP_NAME | cut -d "." -f 1`

          # force the same projection used to download the data (Geography/SIRGAS2000)
          EPSG="4674"

          # If table exists change command to append mode
          if [[ "$CREATE_TABLE" = "YES" ]]; then
              SHP2PGSQL_OPTIONS="-c -s $EPSG:4674 -W 'LATIN1' -g geometries"
              CREATE_TABLE="NO"
          else
              SHP2PGSQL_OPTIONS="-a -s $EPSG:4674 -W 'LATIN1' -g geometries"
          fi

          # import shapefiles
          if $PG_BIN/shp2pgsql $SHP2PGSQL_OPTIONS $DATA_TARGET/$SHP_NAME $TARGET | $PG_BIN/psql $PG_CON
          then
              echo "Import ($FILE_NAME) ... OK" >> $LOGFILE
              rm $DATA_TARGET/$SHP_NAME.{dbf,prj,shp,shx,cst}
              rm $DATA_TARGET/"wfsrequest.txt"
          else
              echo "Import ($FILE_NAME) ... FAIL" >> $LOGFILE
              exit
          fi
        done
      done
      # If the execution arrives here, all the data has been imported. 
      $PG_BIN/psql $PG_CON -t -c "$INSERT_INFOS"
      
      # copy new data to output table
      $PG_BIN/psql $PG_CON -t -c "$INSERT"

      # update biome information for new data into output table 
      $PG_BIN/psql $PG_CON -t -c "$UPDATE"

    fi;# end of shapefile test
  fi;# end numberMatched==row_count
  rm "$DATA_TARGET/acquisition_data_control"
else
  echo "No have data for $TARGET" >> $LOGFILE
fi;