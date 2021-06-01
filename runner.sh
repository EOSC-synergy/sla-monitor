#!/bin/bash

STYLE_FILE=`dirname $0`/style_internal_css.html

REMOTE="marcus@cvs.data.kit.edu:~/public_html/sla-monitor/"
METRICS_DIR="metrics/"

CUR_YEAR=`date +%y`
CUR_MONTH=`date +%m`
CUR_DAY=`date +%d`
CUR_HOUR=`date +%H`
CUR_MIN=`date +%M`

DATESTR=${CUR_YEAR}${CUR_MONTH}${CUR_DAY}-${CUR_HOUR}${CUR_MIN}
HTML_DATESTR="${CUR_DAY}.${CUR_MONTH}.${CUR_YEAR} ${CUR_HOUR}:${CUR_MIN}"


#JSON_FILE="${METRICS_DIR}sla-${DATESTR}.json"
QUOTA_MD_FILE="${METRICS_DIR}sla-${DATESTR}.md"
QUOTA_HTML_FILE="${METRICS_DIR}sla-${DATESTR}.html"
FLAVOR_MD_FILE="${METRICS_DIR}fla-${DATESTR}.md"
FLAVOR_HTML_FILE="${METRICS_DIR}fla-${DATESTR}.html"


./collect-sla-metrics.py -o $QUOTA_MD_FILE -f $FLAVOR_MD_FILE


# SLA / QUOTA
cat $STYLE_FILE > $QUOTA_HTML_FILE
echo "Last updated on ${HTML_DATESTR}<br/>" >> $QUOTA_HTML_FILE
pandoc -f gfm -t html $QUOTA_MD_FILE >> $QUOTA_HTML_FILE

test -e ${METRICS_DIR}index.html && rm ${METRICS_DIR}index.html
cp $QUOTA_HTML_FILE ${METRICS_DIR}index.html


# FLA / FLAVOR
cat $STYLE_FILE > $FLAVOR_HTML_FILE
echo "Last updated on ${HTML_DATESTR}<br/>" >> $FLAVOR_HTML_FILE
pandoc -f gfm -t html $FLAVOR_MD_FILE >> $FLAVOR_HTML_FILE

test -e ${METRICS_DIR}fla-index.html && rm ${METRICS_DIR}fla-index.html
cp $FLAVOR_HTML_FILE ${METRICS_DIR}fla-index.html


# RSYNC
rsync ${METRICS_DIR}sla*html ${METRICS_DIR}fla*html ${METRICS_DIR}index.html $REMOTE
echo "done for $HTML_DATESTR"

