#!/usr/bin/env python3
'''read json and write markdown table'''

import json
import argparse
from sys import stdout, stderr

def parseOptions():
    '''Parse the commandline options'''
    parser = argparse.ArgumentParser(description='None :)')
    parser.add_argument('--verbose','-v', dest='verbose', action='count', default=0)
    parser.add_argument('--inputfile','--input', '-i', default=None)
    args = parser.parse_args()
    return args
args = parseOptions()

with open(args.inputfile,"r") as f:
    jsonstring = f.read()
metrics = [  "cores", "ram", "instances", "gigabytes", "floating-ips", "fixed-ips"]

data = json.loads(jsonstring)
allvos={}

# print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))

# collect available VOs
for site in data.keys():
    for vo in data[site].keys():
        if vo not in ["mteam.data.kit.edu"]:
            allvos[vo]=True

# Dump the tables

for metric in metrics:

    stdout.write(F"| {metric} |")
    for vo in allvos:
        stdout.write(F" {vo.split('.')[0]} |")
    print("")
    for vo in allvos:
        stdout.write("|-------------------------")
    print("|---|")
    for site in data.keys():
        stdout.write(F"| {site}| ")
        for vo in allvos:
            if data[site].get(vo):
                stdout.write(F"    {data[site].get(vo)[metric]}|")
            else:
                stdout.write(F"    | ")
        print("")
    print ("\n\n")
