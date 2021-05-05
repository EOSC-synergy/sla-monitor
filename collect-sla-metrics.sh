#!/bin/bash



IDENTITIES="egi
egi-lago"

SITES=`fedcloud site list`
SITES=CETA-GRID
OUTPUT="out.json"

IFS='
'

OWN_VOS=""

for IDENTITY in $IDENTITIES; do
    echo IDENTITY: ${IDENTITY}
    export OIDC_AGENT_ACCOUNT=${IDENTITY}
    OWN_VOS="${OWN_VOS} `fedcloud token list-vos | sort -u`"
done

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

  for IDENTITY in $IDENTITIES; do
    export OIDC_AGENT_ACCOUNT=${IDENTITY}

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

  done # IDENTITY


    echo "  }" >> $OUTPUT
done # site
echo -e "\n}\n" >> $OUTPUT
