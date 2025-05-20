FRANCE_FILE_PATH="./france-latest.osm.pbf"
RAW_PBF_FILE_PATH="./smdh.osm.pbf"
FINAL_OUTPUT_FILE_PATH="./smdh.osm.xml"

osmium extract -p smdh.geojson --overwrite -f pbf -o $RAW_PBF_FILE_PATH $FRANCE_FILE_PATH

consecutive_filters=(
    "wr/building"
    # "wr/wall!=no"
    # "wr/building!=ruins"
    # "wr/building!=construction"
    # "wr/building!=static_caravan"
    # "wr/building!=ger"
    # "wr/building!=collapsed"
    # "wr/building!=tent"
    # "wr/building!=tomb"
    # "wr/building!=abandoned"
    # "wr/building!=mobile_home"
    # "wr/building!=proposed"
    # "wr/building!=destroyed"
    # "wr/building!=roof"
    # "wr/building!=no"
)

TEMP_FILE_PATH="./temp.osm.pbf"
NEXT_TEMP_FILE_PATH="./next_temp.osm.pbf"

cp $RAW_PBF_FILE_PATH $TEMP_FILE_PATH

for filter in "${consecutive_filters[@]}"; do
    ls -lh $TEMP_FILE_PATH $NEXT_TEMP_FILE_PATH 
    echo "Filtering $filter"
    osmium tags-filter --overwrite $TEMP_FILE_PATH -f pbf -o $NEXT_TEMP_FILE_PATH $filter
    mv $NEXT_TEMP_FILE_PATH $TEMP_FILE_PATH
done

osmium tags-filter $TEMP_FILE_PATH --overwrite -f xml -o $FINAL_OUTPUT_FILE_PATH wr/building
