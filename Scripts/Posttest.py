#! /usr/bin/env python3



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

