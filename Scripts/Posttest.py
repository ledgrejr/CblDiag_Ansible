



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