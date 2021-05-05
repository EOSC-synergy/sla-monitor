#!/usr/bin/env python3

import json
import yaml
import sys
import argparse
# import sqlite3
from fedcloudclient.openstack import fedcloud_openstack as fc_openstack
from fedcloudclient import sites as fc_sites
from fedcloudclient import endpoint as fc_endpoint
import liboidcagent as agent

import logging
logger = logging.getLogger(__name__)

def jprint(jsondata, do_print=True):
    '''json printer'''
    retval = json.dumps(jsondata, sort_keys=True, indent=4, separators=(',', ': '))
    if do_print:
        print (retval)
        return ""
    return retval

def yprint(data, do_print=True):
    '''yaml printer'''
    retval = yaml.dump(data)
    if do_print:
        print (retval)
        return ""
    return retval


def parseOptions():
    '''Parse the commandline options'''
    parser = argparse.ArgumentParser(description='collect-sla-statistics')
    parser.add_argument('-o', dest='output',    default='out.md')
    parser.add_argument('-v', dest='verbose',   action='store_true',  default=False)
    parser.add_argument('-f', dest='fedcloudopsbasepath',
        default='/home/marcus/projects/synergy/fedcloud-catchall-operations/sites')
    args = parser.parse_args()
    return args

args = parseOptions()

account_names = ['egi', 'egi-lago']
SYNERGY_VOS = {        
        "lagoproject.net": "egi-lago",
        "eosc-synergy.eu": "egi",
        "covid19.eosc-synergy.eu": "egi",
        "umsa.cerit-sc.cz": "egi",
        "o3as.data.kit.edu": "egi",
        "worsica.vo.incd.pt": "egi",
        "cryoem.instruct-eric.eu": "egi",
        "mswss.ui.savba.sk": "egi"}
        # "training.egi.eu": "egi",
        # "mteam.data.kit.edu"

access_tokens = {an:agent.get_access_token(an) for an in account_names}

sites = fc_sites.list_sites()
# yprint (sites)
# sys.exit(0)

endpoints_raw={}
for account in account_names:
    for site in sites:
        # if type(endpoints_raw[site]) is not type(list):
        if endpoints_raw.get(site, None) is None:
            endpoints_raw[site] = []
        print (F"{site} via {account}")
        try:
            endpoints_raw[site].extend(fc_endpoint.get_projects_from_sites_dict(access_tokens[account], site))
        except RuntimeError:
            if args.verbose:
                print("Unable to get information from: {site} via {account}")
jprint(endpoints_raw[site])
print (F"site: {site}")

endpoints_from_openstack={}
# transform to fedcloudops-like structure
endpoints_from_openstack[site] = [ {'name': entry['name'], 'auth':{'project_id': entry['project_id']}} for entry in endpoints_raw[site] ]


print (F"endpoints_from_openstack new:")
# yprint(endpoints_from_openstack)
# jprint(endpoints_raw)
jprint(endpoints_from_openstack)


endpoints_from_fedcloudops={}
for site in sites:
    try:
        with open(args.fedcloudopsbasepath+'/'+site+'.yaml', 'r') as file:
            endpoints_from_fedcloudops[site] = yaml.safe_load(file)
    except FileNotFoundError as e:
        # logger.error(F"Cannot find file for {site} in {args.fedcloudopsbasepath}")
        pass

# site_yml=endpoints_from_fedcloudops[sites[inspect]]
# yprint(site_yml)
# jprint(site_yml)
# print (F"\nendpoints fco:")
# jprint (endpoints_from_fedcloudops)


# COMPARE
# report endpoints_from_openstack missing in the fco file

sites_to_rewrite={}
for site in sites:
    missing_at_site = []
    site_needs_update = False
    for vo_from_openstack in endpoints_from_openstack[site]:
        found = False
        for vo_from_fco in endpoints_from_fedcloudops[site]['vos']:
            if vo_from_fco == vo_from_openstack:
                found = True
        if not found:
            site_needs_update = True
            print (F"   Missing at {site}: {vo_from_openstack['name']}")
            missing_at_site.append(vo_from_openstack)
    if site_needs_update:
        jprint(missing_at_site)
        sites_to_rewrite[site]=endpoints_from_fedcloudops[site]
        sites_to_rewrite[site]['vos'].extend(missing_at_site)
yprint(sites_to_rewrite['BIFI'])


sys.exit(0)

vos={}
for site in sites:
    vos[site] = [x["name"] for x in fc_sites.find_site_data(site)["vos"]]

# print (F"VOs: ")
# jprint(vos)
def synergy_filter(vox):
    if vox in SYNERGY_VOS:
        return vox
    return False

# Big Gather loop
site_label = "Site"
vo_label="VO"
error_code_label="error_code"

command = ("quota", "show")
results = {}
print (F"\n{site_label:14} | {vo_label:23} | {error_code_label}")
for site in sites:
    results[site]={}
    for vo in filter(synergy_filter, vos[site]):
        error_code, result = fc_openstack(access_tokens[SYNERGY_VOS[vo]], site, vo, command)
        results[site][vo] = result
        print (F"{site:14} | {vo:23} | {error_code}")

# jprint (results)

# Output loop
METRICS=['cores', 'ram', 'instances', 'gigabytes', 'floating-ips']



output=open(args.output, "w")
for metric in METRICS:
    errors=[]
    # print (F"{metric}")
    # Table header
    output.write(F"| {metric} |")
    # for vo in filter(synergy_filter, vos[site][:2]):
    for vo in SYNERGY_VOS:
        output.write(F" {vo.split('.')[0]} |")

    output.write("\n|---|")
    for vo in SYNERGY_VOS:
        output.write(F"---|")
    output.write("\n")

    # Table body
    for site in results:
        output.write(F"| {site} |")
        for vo in SYNERGY_VOS:
            # print (F"{site:10} | {vo:23}")
            try:
                value=results[site][vo][metric]
            except KeyError:
                value=""
            except TypeError:
                try:
                    errors.append(F"Error {len(errors)+1}: {results[site][vo]}")
                    value=F"Error {len(errors)})"
                except Exception:
                    value="Total Mess"
            output.write(F" {value} |")
        output.write("\n")
    output.write("\n")
    if metric == "cores":
        output.write("\n".join(errors))
    output.write("\n")
output.close()
