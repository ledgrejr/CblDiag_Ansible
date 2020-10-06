#! /usr/bin/env python3

import os
import sys
vendor_dir = os.path.join('../', 'py_libs/')
sys.path.append(vendor_dir)
import yaml 
import json
import csv
import argparse

# pull raw data from ansible output
def getraw(rawdata):
    print (rawdata)
    #print (rawdata['skipped'])
    try:
        print('Raw data found')
        return((rawdata['stdout_lines']))
    except:
        try:
            print('Raw data missing')
            if rawdata['skipped'] == True:
                return ("skipped")
        except: 
            print ('[*] ****rawdata issue*****')
            exit()


def interfacebrief_parse(intbriefdata):
    #print (intdata)
    sw_brief_Int_Dict = {}
    for u in intbriefdata:
        u = u.replace('|','')
        print (u)
        u = u.replace('.','')
        portBrieDict = {}
        #print (u)
        if 'Status' in u or 'Port' in u or '-----' in u or 'Flow' in u or u == "" or 'Attempting' in u:
            continue
        else:
            uspl = u.split()
            #print (len(uspl))
            if (len(uspl)) == 9:
                portBrieDict['Type']= uspl[1]
                portBrieDict['Enabled']= uspl[3]
                portBrieDict['Status']= uspl[4]
                portBrieDict['Mode']= uspl[5]  
            elif (len(uspl)) == 6:
                portBrieDict['Type']= "MIA"
                portBrieDict['Enabled']= uspl[2]
                portBrieDict['Status']= uspl[3]
                portBrieDict['Mode']= uspl[4] 
            else:
                print (len(uspl))
            #print (uspl)
        sw_brief_Int_Dict[uspl[0]]= portBrieDict
    #print (sw_brief_Int_Dict)
    return (sw_brief_Int_Dict)

results_folder = '../Results/'
inv_folder = '../Inv/'

# Arg Parse Main start
# Parse Command Line Arguments
parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(
        description='Basic Discription: Script to generate CSV report from the output of Ansible CableDiag playbook')
#group set up for further development
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-i","--invintory", help="Input file", type=str)
parser.add_argument("-f","--file", help="report filename if differant then inv file", type=str)
parser.add_argument("-v", help="Verbose Output", action="store_true")
args = parser.parse_args()

# gather files. If no output file is selected, will write with invintorey filename (as csv and raw.json)
inv_file = args.invintory
if args.file:
    rep_file = '../Reports/Tests' + args.file

else:
    rep_file = '../Reports/Tests' + inv_file.replace('.yml','.csv')


inv_path = inv_folder + inv_file
try:
    with open(inv_path,'r') as file:
        devlst = yaml.load(file,Loader=yaml.FullLoader)
except:
    print ("[*] Error Could not find invintory file")
    exit()



inv_dict = devlst['all']

idf_lst = []
mdf_lst = []
final_dict = {}
for idfs in (inv_dict['children']['idf']['hosts']):
    idf_lst.append(idfs)
for mdfs in (inv_dict['children']['mdf']['hosts']):
    mdf_lst.append(mdfs)

for idf in idf_lst:

    prefilename = results_folder + idf + '.pretest'
    #print (prefilename)
    postfilename = results_folder + idf + '.posttest'
    #print (postfilename)
    try:
        with open(prefilename,'r') as prefile:
            preraw = getraw(json.loads(prefile.read()))
    
    except:
        print('[!] Missing Pre test file. SKIPPING {}'.format(prefilename))
        continue

    try:
        with open(postfilename,'r') as postfile:
            postraw = getraw(json.loads(postfile.read()))
    except:
        print('[!] Missing post test file. SKIPPING {}'.format(postfilename))
        continue
    preparsed = interfacebrief_parse(preraw)
    print (preparsed)
    postparsed = interfacebrief_parse(postraw)
    print (postparsed)
    for port in preparsed:
        print('Switch {} port {} Pre-status {} post status {}'.format (idf, port, preparsed[port]['Status'],postparsed[port]['Status']))
