#!/bin/usr/env python3

import os
import sys
vendor_dir = os.path.join('../', 'py_libs/')
sys.path.append(vendor_dir)
import yaml 
import json
import csv
import argparse


'''
Versioning: 
    1.0 Inital script 
    1.1 added cmd options for inv and report files 
    
'''
############################################################################################
#Script to generate CSV report from the output of Ansible CableDiag playbook
#
#
############################################################################################
__author__ = "Jay McNealy"
__copyright__ = "None"
__credits__ = ["Jay McNealy"]
__license__ = "GPL"
__version__ = "1.1"
__maintainer__ = "Jay McNealy"
__email__ = "justin.mcnealy@hpe.com"
__status__ = "Testing"
############################################################################################


# pull raw data from ansible output
def getraw(rawdata):
    # print (rawdata['stdout_lines'])

    return((rawdata['stdout_lines']))

# create Dict from raw cable diagnostic data
def cbldiag_parse(cbldata):
    portdict = {}
    #print (type(data))
    for q in cbldata:
        
        if '1-2' in q: 
            qsp = q.split()
            port = qsp[0]
            porttup = qsp[1],qsp[2],qsp[3]
            portdict[port]= [(porttup)]
            #print (qsp)
        elif '3-6' in q or '4-5' in q or '7-8' in q:
            qsp = q.split()
            porttup = qsp[0],qsp[1],qsp[2]
            portdict[port].append(porttup)
    return (portdict)

# create Dict from raw mac address data
def macaddress_parse(macdata):
    #print (macdata)
    with open('mac_oui.json','r') as tempoui:
        ouidict = json.loads(tempoui.read())
    macdict = {}
    for w in macdata:
        #print (w)
        if 'Status' in w or 'MAC Address' in w or '-----' in w or w == "" or 'Attempting' in w:
            continue
        else:
            wspl = w.split()
            #print (wspl)
            mac = (wspl[0])
            macslt = mac.split('-')
            pre_oui = macslt[0]
            try:
                #print (ouidict[pre_oui])
                oui = ouidict[pre_oui]
            except:
                oui = 'Not Found'
            if 'Trk' not in wspl[1]:
                macdict[wspl[1]] =  (wspl[0],wspl[2],oui)
    #print (json.dumps(macdict,indent=2))
    return (macdict)

# create Dict from raw interface data (idf)
def interface_parse(intdata):
    #print (intdata)
    sw_Int_Dict = {}
    for e in intdata:
        #print (e)
        portdict = {}
        if 'Status' in e or 'Port' in e or '-----' in e or 'Flow' in e or e == "" or 'Attempting' in e or 'show'in e:
            continue
        else:
        
            espl = e.split()
            portdict['Tot_Bytes']= espl[1]
            portdict['Tot_Frames']= espl[2]
            portdict['Err_RX']= espl[3]
            portdict['Drop_TX']= espl[4]
        sw_Int_Dict[espl[0]]=portdict
    return (sw_Int_Dict)

# create Dict from raw Interface data (MDF)
def mdf_interface_parse(intdata):
    #print (intdata)
    sw_Int_Dict = {}
    for e in intdata:
        #print (e)
        portdict = {}
        if 'Status' in e or 'Port' in e or '-----' in e or 'Flow' in e or e == "" or 'Attempting' in e or 'show' in e:
            continue
        else:
            espl = e.split()
            print (espl)
            portdict['Tot_Bytes']= espl[1]
            portdict['Tot_Frames']= espl[2]
            portdict['Err_RX']= espl[3]
            portdict['Drop_TX']= espl[4]
        sw_Int_Dict[espl[0]]=portdict
    return (sw_Int_Dict)

# create Dict from raw interface brief data 
def interfacebrief_parse(intbriefdata):
    #print (intdata)
    sw_brief_Int_Dict = {}
    for u in intbriefdata:
        u = u.replace('|','')
        #print (u)
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

# Create Dict from raw poe data
def poe_parse(poedata):
    poedict = {}
    for poeline in poedata:
        if '----' in poeline or 'Port' in poeline or 'Member' in poeline or 'Remaining' in poeline or poeline == "" or 'Refer' in poeline or 'Status' in poeline:
            continue
        else:
            poelinespt = poeline.split()
            #print (poelinespt)
            # key is port number. tuple is ( POE enabled, Delivering )
            poedict[poelinespt[0]]= (poelinespt[1],poelinespt[10])
    #print (json.dumps(poedict,indent=2))
    return (poedict)

# combine all dicte into 1 with interface as index 
def combine_dict(cable,macadd,interface,brief,poe):
    for r in interface:
        #print (r)
        try:
            #print ('match Mac')
            interface[r]['macaddr'] = (macadd[r])
        except:
            interface[r]['macaddr'] = 'N/A'
        # print (macadd[r])
        try:
           #print('match cable')
           interface[r]['cablediag'] = (cable[r])
           #print ('Mac Fount for {}'.format (r))
        except:
            interface[r]['cablediag'] = 'N/A'
        try:
            interface[r]['intBrief'] = brief[r]
        except:
            interface[r]['intBrief'] = "Missing"
        try:
            interface[r]['poe'] = poe[r]
        except:
            interface[r]['poe'] = "N/A"

    return(interface)

# pull info from combine to create csv dict then write line to file 
def csvstarter(csvdata,rep_file):
        #CSV formating and header
        csvfile = open(rep_file, 'w', newline='')
        csv_columns = ['switch','port','Tot Bytes','Tot Frames','Err RX',\
                        'TX Drop','Mac','Mac vendor','Mac Vlan','Enabled','Status','Mode','poe','D_1-2 stat','D_1-2 length',\
                        'D_3-6 stat','D_3-6 length','D_4-5 stat','D_4-5 length','D_7-8 stat','D_7-8 length']
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for a in csvdata:
            csv_dict ={}
            csv_dict['switch'] = a
            #print (a)
            for s in csvdata[a]:
                portdata = csvdata[a][s]
                #print (portdata)
                csv_dict['port'] = "- " + s + " -"
                csv_dict['Tot Bytes'] = portdata['Tot_Bytes']
                csv_dict['Tot Frames'] = portdata['Tot_Frames']
                csv_dict['Err RX'] = portdata['Err_RX']
                csv_dict['TX Drop'] = portdata['Drop_TX']
                if portdata['macaddr'] == 'N/A':
                    csv_dict['Mac'] = 'N/A'
                    csv_dict['Mac Vlan'] = 'N/A'
                    csv_dict['Mac vendor'] = 'N/A'
                else: 
                    csv_dict['Mac'] = portdata['macaddr'][0]
                    csv_dict['Mac Vlan'] = portdata['macaddr'][1]
                    csv_dict['Mac vendor'] = portdata['macaddr'][2]
                csv_dict['Enabled'] = portdata['intBrief']['Enabled']
                csv_dict['Status'] = portdata['intBrief']['Status']
                csv_dict['Mode'] = portdata['intBrief']['Mode']
                csv_dict['poe'] = portdata['poe'][1]
                #print (portdata['intBrief']['Status'])
                if portdata['cablediag'] == 'N/A':
                    csv_dict['D_1-2 stat'] = 'N/A'
                    csv_dict['D_1-2 length'] = 'N/A'
                    csv_dict['D_3-6 stat'] = 'N/A'
                    csv_dict['D_3-6 length'] = 'N/A'
                    csv_dict['D_4-5 stat'] = 'N/A'
                    csv_dict['D_4-5 length'] = 'N/A'
                    csv_dict['D_7-8 stat'] = 'N/A'
                    csv_dict['D_7-8 length'] = 'N/A'
                else:
                    #print (portdata['cablediag'][0][1])
                    csv_dict['D_1-2 stat'] = portdata['cablediag'][0][1]
                    csv_dict['D_1-2 length'] = portdata['cablediag'][0][2]
                    csv_dict['D_3-6 stat'] = portdata['cablediag'][1][1]
                    csv_dict['D_3-6 length'] = portdata['cablediag'][1][2]
                    csv_dict['D_4-5 stat'] = portdata['cablediag'][2][1]
                    csv_dict['D_4-5 length'] = portdata['cablediag'][2][2]
                    csv_dict['D_7-8 stat'] = portdata['cablediag'][3][1]
                    csv_dict['D_7-8 length'] = portdata['cablediag'][3][2]
                writer.writerow(csv_dict)
        return()




results_folder = '../Results/'
inv_folder = '../Inv/'

# Arg Parse Main start
# Parse Command Line Arguments
parser = argparse.ArgumentParser()
parser = argparse.ArgumentParser(
        description='Basic Discription: This script will use Aruba Central APIs to generate yaml invintory with hostname, ports, and mgmt ip for THD stores')
#group set up for further development
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-i","--invintory", help="Input file", type=str)
parser.add_argument("-f","--file", help="report filename if differant then inv file", type=str)
parser.add_argument("-v", help="Verbose Output", action="store_true")
args = parser.parse_args()

# gather files. If no output file is selected, will write with invintorey filename (as csv and raw.json)
inv_file = args.invintory
if args.file:
    rep_file = '/Reports/' + args.file
    raw_file = '/Reports/Raw' + args.file + 'raw.json'
else:
    rep_file = '/Reports/' + inv_file.replace('.yml','.csv')
    raw_file = '/Reports/Raw' + inv_file.replace('.yml','raw.json')

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
    try:
        filename = results_folder + idf + '.cable'
        print (filename)
        with open(filename, 'r') as idffile:
            cableraw = getraw(json.loads(idffile.read()))
    except:
        print ("filenotfound")
    try:
        filename = results_folder + idf + '.interface'
        with open(filename, 'r') as idffile:
            interfaceraw = getraw(json.loads(idffile.read()))
    except:
        print ("filenotfound")
    try:
        filename = results_folder + idf + '.interfacebrie'
        with open(filename, 'r') as idffile:
            intbriraw = getraw(json.loads(idffile.read()))
    except:
        print ("filenotfound")
    try:
        filename = results_folder + idf + '.macaddress'
        with open(filename, 'r') as idffile:
            macraw = getraw(json.loads(idffile.read()))
    except:
        print ("filenotfound")
    try:
        filename = results_folder + idf + '.poe'
        with open(filename, 'r') as idffile:
            poeraw = getraw(json.loads(idffile.read()))
    except:
        print ("filenotfound")
    cabldict = cbldiag_parse(cableraw)
    macadd_dict = macaddress_parse(macraw)
    int_dict = interface_parse(interfaceraw)
    int_brief_dict = interfacebrief_parse(intbriraw)
    poe_dict = poe_parse(poeraw)
    final_dict[idf] = combine_dict(cabldict,macadd_dict,int_dict,int_brief_dict,poe_dict)

for mdf in mdf_lst:
    mac_table = None
    int_brief = None
    int_stat = None
    Cbldiag = None
    try:
        filename = results_folder + mdf + '.cable'
        with open(filename, 'r') as idffile:
            cableraw = getraw(json.loads(idffile.read()))
    except:
        print ("filenotfound")
    try:
        filename = results_folder + mdf + '.interface'
        with open(filename, 'r') as idffile:
            interfaceraw = getraw(json.loads(idffile.read()))
    except:
        print ("filenotfound")
    try:
        filename = results_folder + mdf + '.interfacebrie'
        with open(filename, 'r') as idffile:
            intbriraw = getraw(json.loads(idffile.read()))
    except:
        print ("filenotfound")
    try:
        filename = results_folder + mdf + '.macaddress'
        with open(filename, 'r') as idffile:
            macraw = getraw(json.loads(idffile.read()))
    except:
        print ("filenotfound")
    try:
        filename = results_folder + mdf + '.poe'
        with open(filename, 'r') as idffile:
            poeraw = getraw(json.loads(idffile.read()))
    except:
        print ("filenotfound")
    cabldict = cbldiag_parse(cableraw)
    macadd_dict = macaddress_parse(macraw)
    int_dict = interface_parse(interfaceraw)
    int_brief_dict = interfacebrief_parse(intbriraw)
    poe_dict = poe_parse(poeraw)
    final_dict[mdf] = combine_dict(cabldict,macadd_dict,int_dict,int_brief_dict,poe_dict)
with open(raw_file,'w') as y:
    y.write(json.dumps(final_dict,indent=2))

csvstarter(final_dict,rep_file)