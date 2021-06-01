#!/usr/bin/env python3

import json
import argparse
# import sqlite3
from fedcloudclient.openstack import fedcloud_openstack as fc_openstack
from fedcloudclient import sites as fc_sites
import liboidcagent as agent

def jprint(jsondata, do_print=True):
    '''json printer'''
    retval = json.dumps(jsondata, sort_keys=True, indent=4, separators=(',', ': '))
    if do_print:
        print (retval)
        return ""
    return retval

def write_json_output(data, filename):
    '''write json output'''
    json_file_name = filename.replace('.md', '.json')
    formatted_json_result = jprint (data, do_print = False)
    json_output=open(json_file_name, "w")
    json_output.write(formatted_json_result)
    json_output.close()

def write_md_output_quota(data, filename, METRICS):
    '''write markdown output'''
    filename=filename
    output=open(filename, "w")
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
        for site in data:
            output.write(F"| {site} |")
            for vo in SYNERGY_VOS:
                # print (F"{site:10} | {vo:23}")
                try:
                    value=data[site][vo][metric]
                except KeyError:
                    value=""
                except TypeError:
                    try:
                        errors.append(F"Error {len(errors)+1}: {data[site][vo]}")
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

def write_md_output_flavor(data, filename, METRICS):
    '''write markdown output'''
    output=open(filename, "w")
    for site in data:
        for vo in SYNERGY_VOS:
            errors=[]
            # Table header
            try:
                _ = data[site][vo][0]

                output.write(F"| {site} / {vo.split('.')[0]} |")
                for metric in METRICS:
                    output.write(F" {metric} |")

                output.write("\n|---|")
                for metric in METRICS:
                    output.write(F"---|")
                output.write("\n")

                # Table body
                for flavor_index in range(0,len(data[site][vo])):
                    output.write("| ")
                    for metric in METRICS:
                        output.write(F"| {data[site][vo][flavor_index][metric]}")
                    output.write("|\n")
                output.write("\n")
            except KeyError:
                # print (F"{vo} is not available for {site}")
                pass
    output.close


def parseOptions():
    '''Parse the commandline options'''
    parser = argparse.ArgumentParser(description='collect-sla-statistics')
    parser.add_argument('-o', dest='output',    default='metrics/out.md')
    parser.add_argument('-f', dest='flavor',    default='metrics/flavor.md')
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

quota_command = ("quota", "show")
quotas = {}
flavor_command = ("flavor", "list")
flavors = {}
print (F"\n{site_label:14} | {vo_label:23} | {error_code_label} | Type")
for site in sites:
    quotas[site]={}
    flavors[site]={}
    for vo in filter(synergy_filter, vos[site]):
        error_code, result = fc_openstack(access_tokens[SYNERGY_VOS[vo]], site, vo, quota_command)
        quotas[site][vo] = result
        print (F"{site:14} | {vo:23} | {error_code:10} | q")
        error_code, flavor = fc_openstack(access_tokens[SYNERGY_VOS[vo]], site, vo, flavor_command)
        flavors[site][vo] = flavor
        print (F"{site:14} | {vo:23} | {error_code:10} |   f")

# Write json output

write_json_output(quotas, args.output)
write_json_output(flavors, args.flavor)

# json_input = open('flavor.json', 'r')
# flavors = json.loads(json_input.read())
# json_input.close()

# Output loop
METRICS=['cores', 'ram', 'instances', 'gigabytes', 'floating-ips']

write_md_output_quota(quotas, args.output, METRICS)
write_md_output_flavor(flavors, args.flavor, ['Name', 'RAM', 'Disk', 'Ephemeral', 'VCPUs', 'Is Public', 'ID'])

