#!/bin/bash

STYLE_FILE=`dirname $0`/style_internal_css.html

CUR_YEAR=`date +%y`
CUR_MONTH=`date +%m`
CUR_DAY=`date +%d`

DATESTR=${CUR_YEAR}${CUR_MONTH}${CUR_DAY}

JSON_FILE="sla-${DATESTR}.json"
MD_FILE="sla-${DATESTR}.md"
HTML_FILE="sla-${DATESTR}.html"


./collect-sla-metrics.sh

mv out.json $JSON_FILE

./json-to-table.py --input $JSON_FILE > $MD_FILE

cat $STYLE_FILE > $HTML_FILE
pandoc -f gfm -t html $MD_FILE >> $HTML_FILE

