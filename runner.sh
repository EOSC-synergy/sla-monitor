#!/bin/bash

STYLE_FILE=`dirname $0`/style_internal_css.html

REMOTE="marcus@cvs.data.kit.edu:~/public_html/sla-monitor/"
METRICS_DIR="metrics"

CUR_YEAR=`date +%y`
CUR_MONTH=`date +%m`
CUR_DAY=`date +%d`
CUR_HOUR=`date +%H`
CUR_MIN=`date +%M`

DATESTR=${CUR_YEAR}${CUR_MONTH}${CUR_DAY}-${CUR_HOUR}${CUR_MIN}

JSON_FILE="${METRICS_DIR}sla-${DATESTR}.json"
MD_FILE="${METRICS_DIR}sla-${DATESTR}.md"
HTML_FILE="${METRICS_DIR}sla-${DATESTR}.html"


./collect-sla-metrics.py -o $MD_FILE

#mv out.json $JSON_FILE
#
#./json-to-table.py --input $JSON_FILE > $MD_FILE

cat $STYLE_FILE > $HTML_FILE
pandoc -f gfm -t html $MD_FILE >> $HTML_FILE

test -e ${METRICS_DIR}index.html && rm ${METRICS_DIR}index.html
cp $HTML_FILE ${METRICS_DIR}index.html

rsync ${METRICS_DIR}sla*html ${METRICS_DIR}index.html $REMOTE

