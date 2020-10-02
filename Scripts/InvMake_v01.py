#!/usr/bin/env python3

import os
import sys
vendor_dir = os.path.join('../', 'py_libs/')
sys.path.append(vendor_dir)
import requests
import json
import configparser
import ast
import argparse
import getpass
import logging
import time
#from datetime import datetime
import datetime
from subprocess import check_output
from collections import defaultdict
import yaml


'''
TODO notes:

Adjust logging 
Add store validation 
'''

__author__ = "Jay McNealy"
__copyright__ = "None"
__credits__ = ["Jay McNealy"]
__license__ = "GPL"
__version__ = "1.0"
__maintainer__ = "Jay McNealy"
__email__ = "justin.mcnealy@hpe.com"
__status__ = "Testing"

# Logging
def init_logging():

    'Initialize Logging Globally'

    # Specify our log format for handlers
    log_format = logging.Formatter('%(asctime)s %(name)s:%(levelname)s: %(message)s')

    # Get the root_logger to attach log handlers to
    root_logger = logging.getLogger()

    # Set root logger to debug level always
    # Control log levels at log handler level
    root_logger.setLevel(logging.DEBUG)

    # Console Handler (always use log_level)
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(log_format)
    root_logger.addHandler(ch)


    # Logfile Handler
    fh = logging.FileHandler(config['main']['log_file'])

    # Always log at INFO or below
    if log_level < logging.INFO:
        fh.setLevel(log_level)
    else:
        fh.setLevel(logging.INFO)

    # Attach logfile handler
    fh.setFormatter(log_format)
    root_logger.addHandler(fh)

# Central API to get list of switches for group
def get_switches(host,group,token):
    url = host +"/monitoring/v1/switches?group="+group+"&show_resource_details=true"
    #print (url)
    payload = {}
    headers = {
    'Authorization': 'bearer %s'%token
    }

    response = requests.request("GET", url, headers=headers, data = payload)
    if response.status_code == 200:
        logger.info(response.text.encode('utf8'))
        switches_json = json.loads(response.text.encode('utf8'))
        print('[+] Get Switches API returned with status code 200')
        return(switches_json["switches"])
    else:
        logger.warning ("[-] Error: Get_Switches API call did not return with response code 200")
        logger.warning (response.text)
        logger.warning ("ERROR 14")
        print ("[-] Error: Get_Switches API call did not return with response code 200")
        sys.exit()

# Central api to get group from search string
def get_group(host,srch,token):
    url = host +"/configuration/v1/groups?limit=20&offset=0&q="+srch
    #print (token)
    payload = {}
    headers = {
    'Authorization': 'bearer %s'%token
    }

    response = requests.request("GET", url, headers=headers, data = payload)
    #return(True)
    logger.info(response.text.encode('utf8'))
    if response.status_code == 200:
        logger.info(response.text.encode('utf8'))
        resp_json = json.loads(response.text.encode('utf8'))
        if len(resp_json['data']) > 1 or len(resp_json['data']) == 0:
            print('Search returned {} matches. Please try again with a more spicific search paramiter.'.format(len(resp_json['data'])))
            sys.exit()
            #print(len(resp_json['data']))
        print('[+] Get group API returned with status code 200')
        return(resp_json['data'][0])
    else:
        logger.warning ("[-] Error: Get_Group API call did not reutn with response code 200")
        logger.warning (response.text)
        logger.warning ("ERROR 15")
        print ("[-] Error: Get_Group API call did not reutn with response code 200")
        sys.exit()

# Central API to get vlan 4093 IP address
def get_4093ip(host,swinfo,token):
    if swinfo['stackstat'] is False:
        url = host + "/monitoring/v1/switches/"+swinfo['stack_id']+"/vlan?id=4093"
    else:
        url = host +"/monitoring/v1/switch_stacks/"+swinfo['stack_id']+"/vlan?id=4093"
    #print (url)
    payload = {}
    headers = {
    'Authorization': 'bearer %s'%token
    }

    response = requests.request("GET", url, headers=headers, data = payload)
    #return(True)
    response_json = json.loads(response.text)
    if response.status_code == 200:
        response_json = json.loads(response.text)
        logger.info(response.text)
        #print (response_json.keys())
        vlans = response_json['vlans']
        print('[+] Get vlan 4093 ip address API returned with status code 200')
        return(vlans[0]['ipaddress'])
    else:
        logger.warning ("[-] Error: Get_4093ip API call did not reutn with response code 200")
        logger.warning (response.text)
        logger.warning ("ERROR 16")
        print ("[-] Error: Get_4093ip API call did not reutn with response code 200")
        sys.exit()

# Central API to "RJ-45" ports form MDF 
def get_mdfports(host,data,token):
    ports = []
    for sw in data:
        #print(sw[2])
        url = host + '/monitoring/v1/switches/'+ sw[2] +'/ports'
        #print (url)
        payload = {}
        headers = {
        'Authorization': 'bearer %s'%token
        }

        response = requests.request("GET", url, headers=headers, data = payload)
        if response.status_code == 200:
            logger.info(response.text)
            switches_json = json.loads(response.text)
            returnedports = mdfportparser(switches_json)

            ports += returnedports

        else:
            logger.warning ("[-] Error: get_MDFports API call did not reutn with response code 200")
            logger.warning (response.text)
            logger.warning ("ERROR 17")
            print ("[-] Error: get_MDFports API call did not reutn with response code 200")
            sys.exit()
    portsstr = ",".join(ports)
    print('[+] Get mdf ports returned with status code 200')
    return(portsstr)

# function to process get_mdfports data
def mdfportparser(mdfdata):
    singleports = []
    #print (data['ports'])
    print('[+] Parsing data from MDF port API call')
    for port in mdfdata['ports']:
        if port['phy_type'] == 'RJ45' and 'oobm' not in port['port_number'] and "A" not in port['port_number'] and "B" not in port['port_number']:
            singleports.append(port['port_number'])
    singlestr= ",".join(singleports)
    #singleste = "\' " + singlestr + " \'"
    #print (singlestr + '\n\n\n\n')
    return (singleports)

# Function to convert IDF models to port lists
def portconverter(idfdata):
    portlist = []
    portstr = ""
    #print ((data))
    print('[+] Get IDF ports from model number')
    for sw in idfdata:
        #print (sw[0])
        if 'J9727A' in sw[0]:
            swports = "{}/1-{}/23".format (sw[1],sw[1])
            portlist.append(swports)
        elif 'JL320A' in sw[0]:
            swports = "{}/1-{}/23".format (sw[1],sw[1])
            portlist.append(swports)
        elif 'JL258A' in sw[0]:
            swports = "{}/1-{}/8".format (sw[1],sw[1])
            portlist.append(swports)
    portstr = ",".join(portlist)
    #portstr = "\" " + portstr + " \""
    #print (portstr)
    ###### Changed portstr to string need to 
    return (portstr)

# Ag function used to build inbvintory Dictionary from get_switches API call
def swData(switches):
    print('[+] Updating Switch Dictionary')
    switchnames =[]
    stackinfo = {}
    storeinfo = {}
    for switch in switches:
        if switch["name"] not in switchnames and switch["status"] != 'Down':
            switchnames.append(switch["name"])
        elif switch["name"] not in switchnames and switch["status"] == 'Down':
            print ('[-] ERROR: Switch not up.{}'.format(switch["name"]))
        else:
            continue
    for swich in switchnames:
        swichinfo = {}
        swichlist = []
        for switch in switches:
            if switch['name'] == swich:
                try:
                    swtup = (switch["model"],switch["stack_member_id"],switch['serial'])
                    swichlist.append(swtup)
                except:
                    swtup = (switch["model"],1,switch['serial'])
                    swichlist.append(swtup)

                #Remove once MDF address is converted to ATT IP address
                if switch["ip_address"] != "":
                    swichinfo['ip'] = switch["ip_address"]
                try:
                    swichinfo['stack_id'] = switch['stack_id']
                    swichinfo['stackstat'] = True
                except:
                    swichinfo['stack_id'] = switch['serial']
                    swichinfo['stackstat'] = False
        swichinfo['switches'] = swichlist
        storeinfo[swich]=swichinfo
    
    return(storeinfo)

# function to write Yaml file from inv Dict
def ymlmaker(mdf,idf):
    iterat1 = {}
    idfs = {}
    mdfs = {}
    devlist = []
    base = {}
    completedict = {}
    idffullsw = {}
    mdffullsw = {}
    for sw in idf:
        intsw = {}
        intsw['ports'] =  sw['ports']
        intsw['ansible_host'] = sw['ip']
        idffullsw[sw['hostname']] = intsw
    for sw in mdf:
        intsw = {}
        intsw['ports'] =  sw['ports']
        intsw['ansible_host'] = sw['ip']
        mdffullsw[sw['hostname']] = intsw
        #devlist.append("{} ansiblehost= {} ports= {} hostname= {}" .format(sw['hostname'],sw['ip'],sw['ports'],sw['hostname']))
    idfs['hosts'] = idffullsw
    #print (json.dumps(mdffullsw,indent=2))
    mdfs['hosts'] = mdffullsw
    base['mdf'] = mdfs
    #print (base['mdf'])
    base['idf'] = idfs
    iterat1['children'] = base
    completedict['all'] = iterat1
    #completedict['all'] = base
    #print (yaml.dump(completedict))
    return (json.dumps(completedict,indent=2))
 
# Main Logging Start ####
logger = logging.getLogger('SwInfo')
# Main logging End ####

# Arg Parse Main start
# Parse Command Line Arguments
parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(
        description='Basic Discription: This script will use Aruba Central APIs to generate yaml invintory with hostname, ports, and mgmt ip for THD stores')
#group set up for further development
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-g","--groupfile", help="Input file", type=str)
parser.add_argument("-f","--file", help="filename of output file. Will be stored in Inv directory", type=str, required=True)
parser.add_argument("-v", help="Verbose Output", action="store_true")
args = parser.parse_args()

# Config Parse Start
#Pull variables from config
CONFIG_FILE = 'config.ini'
# Initialize Config file and get the default log_level
config = configparser.ConfigParser()
config.read(CONFIG_FILE)
log_level = int(config['main']['log_level'])

host = str(config['main']['host'])
token = str(config['main']['token'])
outfile = args.file


if args.v:
    log_level = logging.INFO

#Init logging
init_logging()


if args.groupfile:
    mdfsw = []
    idfsw = []
    filename = args.groupfile
    with open(filename,'r') as f:
        groups = f.readlines()
    for group in groups:
        print('\n\n\n********************************')
        print('[+] Starting API calls for group {} '.format(group))
        grp = group.strip()
        srchsrting = grp
        tggrp = get_group(host,srchsrting,token)
        print('[+] Group search returned  {} '.format(tggrp['group']))
        print('[+] Moving to Switch inv API')
        switches = get_switches(host,tggrp['group'],token)
        #print (switches)
        swinfo = swData(switches)
        #print (swinfo)
        print('[+] Getting switch data')
        for x in swinfo:
            ports = ""
            if "swm" in x:
                print('[+] Found Store MDF')
                #print (swinfo[x])
                ports = get_mdfports(host,swinfo[x]['switches'],token)
                swinfo[x]['ports'] = ports
                swinfo[x]['hostname'] = x
                mdfsw.append(swinfo[x])
                attip = get_4093ip(host,swinfo[x],token)
                swinfo[x]['ip'] = attip
            else:
                ports = portconverter (swinfo[x]['switches'])
                swinfo[x]['ports'] = ports
                swinfo[x]['hostname'] = x
                idfsw.append(swinfo[x])
                #print(swinfo[x].keys())

                attip = get_4093ip(host,swinfo[x],token)
                swinfo[x]['ip'] = attip

    output_file = '../Inv/' + args.file 

    print('[+] Pushing Data for YAML file creation')
    outputdata = ymlmaker(mdfsw,idfsw)
    with open(output_file, 'w') as writefile:
        writefile.write(outputdata)
    print('[+] Invintory file created with filname -->>:  {}'.format(output_file))


