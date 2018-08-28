#/usr/bin/python3.5

#Alex Wen created this script on 2018-01-14 for v0.1
#       Collect hard info: BIOS Version,ModeName,TouchScreen,Camera,dGPU,iGPU,GPUsubSystemID,CarderReader,Network,Bluetooth,Serial#,Touchpad,Memory,EthernetMac,Ethernet,Audio,CPU
#       hard disk info is under construction
#       Need to add manually MTM,Fingerprint,WWAN,EC
#Tested this script on Tachi-P-2, Windu2-2,Raven3-2,Lando-2,all the hardware info can be collected.

import re
import commands
import subprocess
import os

lspciInfo = commands.getoutput('lspci -nnn')
devicesList = ["VGA","Audio","3D controller","Display","Network","Ethernet"]

lsusbInfo = commands.getoutput("lsusb -v")
lsusbList = [""]

DevInfo = {}


hostname = commands.getoutput('hostname')
filename = hostname + '-Hardware_info.txt'   #The hardware info recorded to the file

def Command():
    pass
    

#This class is for lspci command to get the hardware info
class GetInfoFrlspci(object):
    def __init__(self,devStr,devlist = ""):
        self.devStr = devStr
        self.devlist = devlist

    def getContent(self):
        return self.devStr.strip().split('\n')
    
    def getHWfromlist(self):
        return self.getContent()

    def addSameItem(self,item):
        for line in f.readlines():
            if item in line:
            	if DevInfo.has_key(item):
            	    old = DevInfo[item].strip()
               	    new = old + ' ' + '+' + ' ' + line.strip()
              	    DevInfo[item] = new
                else:
                    DevInfo[item] = line
		return DevInfo

    def addItem2Dict(self,dic,key,value):
        if not dic.has_key(key):
	    #if key == 'VGA':
	    #    self.addSameItem(self,key)
            if key == "3D controller" or key == "Display":
                key = "dGPU"
            if key == "Network":
                key = "Wireless"
            dic[key] = value
    
    #Add the info to a dict,DevInfo[hardware] = hardwareValue
    def getInfo(self):
        for line in self.getHWfromlist():
            for devItem in self.devlist:
                if devItem in line:
                    self.addItem2Dict(DevInfo,devItem.strip(),line)
        return DevInfo


#this class is for lsusb command to get the hardeware info
class GetInfoFrlsusb(GetInfoFrlspci):
    def __init__(self,devStr,devlist,tbd):
        super(GetInfoFrlsusb,self).__init__(devStr,devlist)
        self.tbd = tbd

    #get hardware id from lsusb,One known issue. When a usb stick is inserted, the carder reader will be detected to the inserted usb vendor,SandDisk CZ80,CZ40 and Transcend usb can pass.
    def getlsusbID(self):
        return commands.getoutput("""lsusb |egrep -v 'SDCZ80|SDCZ40|Transcend' |awk '{print $6}'""").split('\n')

    #Search the key word from lsusb -v command and return to the hardware id, the id can get the hardware vendor 
    def gethw(self,Searchkey,DictKey):
            for ids in self.getlsusbID():
                s = commands.getoutput("lsusb -v -d %s" %ids)
                if Searchkey in s:
                    value = commands.getoutput("""lsusb |grep %s|awk -F"ID " '{print $2}' 2>/dev/null""" %ids)
                    return self.addItem2Dict(DevInfo,DictKey,value)


dev = GetInfoFrlspci(lspciInfo,devicesList)
lsusb = GetInfoFrlsusb(lsusbInfo,'TBD','TBD')

#get hardware info from /proc and lsusb 
def getiHWfrproc(*args):
    for item in args:
        if item.lower() == "memory":
            value = commands.getoutput("""cat /proc/meminfo |head -1|awk '{print $2/1024/1024"G"}'""")
            dev.addItem2Dict(DevInfo,'Memory',value)
        if item.lower() == "cpu":
            value = commands.getoutput("""cat /proc/cpuinfo|grep "model name"|sort -u|awk -F: '{print $2}'|sed 's/^[ \t]//g'""")
            dev.addItem2Dict(DevInfo,'CPU',value)
        if item.lower() == "gpusubid":
            value = commands.getoutput("lspci -nnn -s 00:02.0 -v |grep Subsystem|sed 's/^[ \t]//g'")
            dev.addItem2Dict(DevInfo,"GPUsubSystemID",value)
        if item.lower() == "mac":
            value = commands.getoutput("""ifconfig |egrep 'enp|eth'|awk '{print $NF}'""")
            dev.addItem2Dict(DevInfo,"EthernetMac",value)
        if item.lower() == "touchpad":
            value = commands.getoutput("""egrep -i 'synap|alps|etps|elan' /proc/bus/input/devices |grep -i 'Name'|grep -i 'TouchPad'|awk -F'=|"' '{print $3}'""")
            dev.addItem2Dict(DevInfo,"Touchpad",value)
        if item.lower() == "bt":
            lsusb.gethw('Bluetooth','Bluetooth')
        if item.lower() == "webcam":
            lsusb.gethw('Video Streaming','Camera')
        if item.lower() == "cardreader":
            lsusb.gethw('Mass Storage','CardReader')
	    if DevInfo.has_key('CardReader'):
	        pass
	    else:
		DevInfo['CardReader']= commands.getoutput("""lspci -nnn|grep -i Card""")
        if item.lower() == "touchscreen":
            lsusb.gethw('Human Interface Device','TouchScreen')
    return DevInfo    


def main():
    dev.getInfo()

    #Add the BIOS info
    DevInfo["Serial#"] = commands.getoutput("sudo dmidecode -s system-serial-number")
    DevInfo["BIOSVersion"] = commands.getoutput("sudo dmidecode -s bios-version")
    DevInfo["ModeName"] = commands.getoutput("sudo dmidecode -s System-Version")
    DevInfo["NVME"] = commands.getoutput("""lspci -nnn |grep "Non-Volatile memory controller"|awk -F":" '{print $3}' """)
    #Following items should be checked from BIOS
    DevInfo['MTM'] = "Please check from BIOS"
    DevInfo['EC'] = "Please check from BIOS"
    DevInfo['WWAN'] = "Please check from BIOS"
    DevInfo['FingerPrint'] = "Please check from BIOS"

    g = getiHWfrproc('Memory','cPu','GPUsubid','MAC','TOUCHPAD','BT','webcam','cardreader','touchscreen')
    
    #get hard disk from lspci

    #get cardreader from lspci
    print "Writing %s hardware info to the file %s." %(hostname,filename)
    for i in DevInfo:
        print "%-15s ===> %-20s" %(i,DevInfo[i])
        with open(filename,'a') as f:
            f.write("%-15s ===> %-20s \n" %(i,DevInfo[i]))
	
if __name__ == '__main__':
    main()

