#!/bin/bash



export OIDC_AGENT_ACCOUNT=egi-lago
SITES=`fedcloud site list`
OUTPUT="out.json"

IFS='
'

OWN_VOS=`fedcloud token list-vos | sort -u`

iscontained(){
    VO=$1
    CONTAINED=1
    for OVO in $OWN_VOS; do
        [ x$VO == x$OVO ] && CONTAINED=0
    done
    #echo "      contained: $CONTAINED"
    return $CONTAINED
}
echo "{" > $OUTPUT
FIRSTSITE="True"
for SITE in $SITES; do
    echo -e "\n$SITE"
    [ $FIRSTSITE == "False" ] && echo "," >> $OUTPUT
    FIRSTSITE="False"
    echo -e "  \"$SITE\": {" >> $OUTPUT
    VOS=`fedcloud site show --site ${SITE}| grep name | cut -d : -f 2 | sed s"/^ //"`
    FIRSTVO="True"
    for VO in $VOS; do
        echo -e "    $VO"
        iscontained $VO && {
            [ $FIRSTVO == "False" ] && echo "," >> $OUTPUT
            FIRSTVO="False"
            echo -en "    \"$VO\": {" >> $OUTPUT
            JSON_SIPPET=`
                fedcloud openstack quota show --site $SITE --vo $VO -f json | \
                grep -v Site | \
                jq '{"cores", "ram", "instances", "gigabytes", "floating-ips", "fixed-ips"}'
            `
            echo -n "$JSON_SIPPET"| sed s/[{}]// | sed s/^/\ \ \ \ / >> $OUTPUT
            echo -n "    }" >> $OUTPUT
            echo -e "---------------------\n${JSON_SIPPET}\n------------------\n"
        } # Contained
    done # VO
    echo "  }" >> $OUTPUT
done # site
echo -e "\n}\n" >> $OUTPUT
