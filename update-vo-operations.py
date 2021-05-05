#!/usr/bin/env python3
# pylint disable=logging-fstring-interpolation
'''
Author: Marcus Hardt <hardt@kit.edu>
Script to compare openstack information with the data in 
https://github.com/EGI-Federation/fedcloud-catchall-operations/tree/main/sites

Requires the git repository to be cloned to a local place that needs to be 
specified with -f <full path>

Requires oidc-agent to be installed

Currently is using two oidc-agent configs: 'egi' and 'egi-lago' and is
limited to the synergy VOs (because my credentials are in all of them)

'''

import json
import yaml
import argparse
import os
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
    parser.add_argument('-v', dest='verbose',   action='store_true',  default=False)
    parser.add_argument('-f', dest='fedcloudopsbasepath',
        default='/home/marcus/projects/synergy/fedcloud-catchall-operations/sites')
    args = parser.parse_args()
    return args

######################################################################
# Config:
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

# Get access tokens from oidc agent
access_tokens = {an:agent.get_access_token(an) for an in account_names}

# Get sites from fedcloudclient
sites = fc_sites.list_sites()

# loop over all sites and accounts
print (F"Loading information via fedcloudclient get projects from sites:")
endpoints_raw={}
for site in sites:
    print (F"    {site}")
    for account in account_names:
        # if type(endpoints_raw[site]) is not type(list):
        if endpoints_raw.get(site, None) is None:
            endpoints_raw[site] = []
        try:
            endpoints_raw[site].extend(fc_endpoint.get_projects_from_sites_dict(access_tokens[account], site))
        except RuntimeError:
            if args.verbose:
                print("Unable to get information from: {site} via {account}")

# transform to fedcloudops-like structure
endpoints_openstack={}
endpoints_openstack[site] = [ {'name': entry['name'], 'auth':{'project_id': entry['project_id']}} for entry in endpoints_raw[site] ]
endpoints_openstack = { site:
        [ {'name': entry['name'], 'auth':{'project_id': entry['project_id']}} for entry in endpoints_raw[site] ]
        for site in sites}

if args.verbose:
    print (F"endpoints_openstack:")
    yprint(endpoints_openstack)

# read fedcloudops

print (F"Loading information from {args.fedcloudopsbasepath}")
endpoints_fedcloudops={}

for yaml_file_name in os.listdir(args.fedcloudopsbasepath):
    if yaml_file_name.endswith('.yaml'):
        if yaml_file_name.endswith('IISAS-FedCloud-nova.yaml'):
            continue
        with open(args.fedcloudopsbasepath+'/'+yaml_file_name, 'r') as file:
            temp = yaml.safe_load(file)
            site_from_file = temp['gocdb']
            endpoints_fedcloudops[site_from_file] = temp
            endpoints_fedcloudops[site_from_file]['filename'] = yaml_file_name

if args.verbose:
    print (F"endpoints_fedcloudops:")
    yprint(endpoints_fedcloudops)

print ("Comparing")

# COMPARE
# report endpoints_openstack missing in the fco file
sites_to_rewrite={}
for site in sites:
    missing_at_site = []
    site_needs_update = False
    for vo_from_openstack in endpoints_openstack[site]:
        found = False
        try:
            fco_endpoints_site_vo = endpoints_fedcloudops[site]['vos']
        except KeyError as e:
            logger.error(F"Openstack site not found in fedcloud-catchall-operations/sites: {site}")
            logger.error("This may be ignored for IISAS-FedCloud (sorry Viet)")
            try:
                fco_endpoints_site_vo = endpoints_fedcloudops[site+'-cloud']['vos']
            except KeyError:
                logger.error(F"cannot load for site {site}")
        for vo_from_fco in fco_endpoints_site_vo:
            if vo_from_fco == vo_from_openstack:
                found = True
        if not found:
            site_needs_update = True
            if args.verbose:
                print (F"   Missing at {site}: {vo_from_openstack['name']}")
            missing_at_site.append(vo_from_openstack)

    if site_needs_update:
        #jprint(missing_at_site)
        sites_to_rewrite[site]=endpoints_fedcloudops[site]
        sites_to_rewrite[site]['vos'].extend(missing_at_site)


print ("Writing")
# write changed sites back
for site,content in sites_to_rewrite.items():
    try:
        yaml_file_name = endpoints_fedcloudops[site]['filename']
        with open(args.fedcloudopsbasepath+'/'+yaml_file_name, 'w') as file:
            yaml.dump(content, file)
    except FileNotFoundError as e:
        # logger.error(F"Cannot find file for {site} in {args.fedcloudopsbasepath}")
        pass
print ("Done")
